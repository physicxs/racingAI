#!/usr/bin/env python3
"""
F1 2025 Live Track Map GUI

Displays a real-time track map with the player car's position.
Reads a pre-built track map JSON and live telemetry from stdin,
or replays a recorded JSONL file.

Controls:
    Scroll wheel    Zoom in/out
    Click + drag    Pan the map
    R               Reset zoom to fit
    F               Follow player car (toggle)
    +/-             Zoom in/out

Replay controls:
    Space           Play / pause
    Left / Right    Skip -5s / +5s
    1 / 2 / 3 / 4  Speed 1x / 2x / 4x / 0.5x
    Click bar       Seek to position

Usage:
    mvn -q exec:java ... 2>&1 | python3 track_map_live.py <track_map.json>
    python3 track_map_live.py <track_map.json> --replay <telemetry.jsonl>
"""

import json
import sys
import math
import time
import threading
import tkinter as tk


# ─── Track Map Loading ────────────────────────────────────────────────────────

def load_track_map(path):
    """Load track map JSON file."""
    with open(path) as f:
        data = json.load(f)
    points = data['points']
    us = [p['u'] for p in points]
    vs = [p['v'] for p in points]
    return {
        'track_id': data.get('track_id'),
        'track_length': data.get('track_length_m', len(points)),
        'u_axis': data.get('coordinate_axes', {}).get('u', 'u'),
        'v_axis': data.get('coordinate_axes', {}).get('v', 'v'),
        'us': us,
        'vs': vs,
        'num_points': len(points),
    }


# ─── Coordinate Transform with Zoom/Pan ──────────────────────────────────────

class CoordTransform:
    """Maps track (u, v) coordinates to canvas pixel coordinates with zoom/pan."""

    def __init__(self, us, vs, canvas_w, canvas_h, margin=50):
        self.canvas_w = canvas_w
        self.canvas_h = canvas_h

        self.min_u, self.max_u = min(us), max(us)
        self.min_v, self.max_v = min(vs), max(vs)

        range_u = self.max_u - self.min_u or 1.0
        range_v = self.max_v - self.min_v or 1.0

        scale_u = (canvas_w - 2 * margin) / range_u
        scale_v = (canvas_h - 2 * margin) / range_v
        self.base_scale = min(scale_u, scale_v)

        # Center of track in track coords
        self.center_u = (self.min_u + self.max_u) / 2.0
        self.center_v = (self.min_v + self.max_v) / 2.0

        # Zoom and pan state
        self.zoom = 1.0
        self.pan_x = 0.0  # pixel offset
        self.pan_y = 0.0

    def to_canvas(self, u, v):
        """Convert track (u, v) to canvas (x, y)."""
        scale = self.base_scale * self.zoom
        cx = (u - self.center_u) * scale + self.canvas_w / 2.0 + self.pan_x
        cy = (v - self.center_v) * scale + self.canvas_h / 2.0 + self.pan_y
        return cx, cy

    def to_track(self, cx, cy):
        """Convert canvas (x, y) back to track (u, v)."""
        scale = self.base_scale * self.zoom
        u = (cx - self.canvas_w / 2.0 - self.pan_x) / scale + self.center_u
        v = (cy - self.canvas_h / 2.0 - self.pan_y) / scale + self.center_v
        return u, v

    def zoom_at(self, factor, cx, cy):
        """Zoom by factor, keeping canvas point (cx, cy) fixed."""
        # Track coord under cursor before zoom
        tu, tv = self.to_track(cx, cy)

        self.zoom *= factor

        # Where that track coord maps after zoom
        new_cx, new_cy = self.to_canvas(tu, tv)

        # Adjust pan so the cursor stays over the same track point
        self.pan_x += cx - new_cx
        self.pan_y += cy - new_cy

    def reset(self, canvas_w, canvas_h):
        """Reset to fit the full track."""
        self.canvas_w = canvas_w
        self.canvas_h = canvas_h
        self.zoom = 1.0
        self.pan_x = 0.0
        self.pan_y = 0.0

    def center_on(self, u, v):
        """Center the view on a track coordinate."""
        scale = self.base_scale * self.zoom
        target_cx = self.canvas_w / 2.0
        target_cy = self.canvas_h / 2.0
        current_cx = (u - self.center_u) * scale + self.canvas_w / 2.0 + self.pan_x
        current_cy = (v - self.center_v) * scale + self.canvas_h / 2.0 + self.pan_y
        self.pan_x += target_cx - current_cx
        self.pan_y += target_cy - current_cy


# ─── Car Position Lookup ─────────────────────────────────────────────────────

def lookup_position(track_map, lap_distance):
    """Look up (u, v) on track map from lap distance with interpolation."""
    n = track_map['num_points']
    if n == 0:
        return 0, 0

    s = lap_distance % track_map['track_length']
    if s < 0:
        s += track_map['track_length']

    i = int(s)
    if i >= n - 1:
        return track_map['us'][-1], track_map['vs'][-1]

    t = s - i
    u = track_map['us'][i] + t * (track_map['us'][i + 1] - track_map['us'][i])
    v = track_map['vs'][i] + t * (track_map['vs'][i + 1] - track_map['vs'][i])
    return u, v


# ─── Stdin Reader Thread ─────────────────────────────────────────────────────

class TelemetryReader:
    """Reads telemetry JSONL from stdin in a background thread."""

    def __init__(self):
        self.latest = None
        self.lock = threading.Lock()
        self.running = True

    def start(self):
        thread = threading.Thread(target=self._read_loop, daemon=True)
        thread.start()

    def _read_loop(self):
        try:
            for line in sys.stdin:
                if not self.running:
                    break
                if not line.startswith('{'):
                    continue
                try:
                    data = json.loads(line.strip())
                    with self.lock:
                        self.latest = data
                except json.JSONDecodeError:
                    pass
        except (KeyboardInterrupt, IOError):
            pass

    def get_latest(self):
        with self.lock:
            data = self.latest
            self.latest = None
            return data

    def stop(self):
        self.running = False


# ─── Replay Reader ──────────────────────────────────────────────────────────

class ReplayReader:
    """Reads telemetry from a recorded JSONL file with playback controls."""

    def __init__(self, path):
        self.frames = []
        self.frame_index = 0
        self.playing = False
        self.speed = 1.0
        self.wall_start = 0.0      # wall-clock time when play started
        self.data_start = 0        # timestamp (ms) of frame at play start
        self.running = True

        self._load(path)

    def _load(self, path):
        with open(path) as f:
            for line in f:
                line = line.strip()
                if not line.startswith('{'):
                    continue
                try:
                    data = json.loads(line)
                    self.frames.append(data)
                except json.JSONDecodeError:
                    pass
        if not self.frames:
            print("ERROR: No telemetry frames found in file")
            sys.exit(1)
        print(f"Loaded {len(self.frames)} frames for replay")

    def start(self):
        """Begin playback immediately."""
        self.playing = True
        self.frame_index = 0
        self._sync_clock()

    def stop(self):
        self.running = False

    def _sync_clock(self):
        """Sync wall clock to current frame position."""
        self.wall_start = time.time()
        self.data_start = self.frames[self.frame_index].get('timestamp', 0)

    def get_latest(self):
        """Return the current frame based on playback timing."""
        if not self.frames:
            return None

        if self.playing:
            elapsed_wall = time.time() - self.wall_start
            elapsed_data = elapsed_wall * self.speed * 1000  # convert to ms
            target_ts = self.data_start + elapsed_data

            # Advance frame_index to match target timestamp
            while (self.frame_index < len(self.frames) - 1 and
                   self.frames[self.frame_index + 1].get('timestamp', 0) <= target_ts):
                self.frame_index += 1

            # Auto-pause at end
            if self.frame_index >= len(self.frames) - 1:
                self.playing = False

        return self.frames[self.frame_index]

    def toggle_play(self):
        if self.playing:
            self.playing = False
        else:
            # If at end, restart from beginning
            if self.frame_index >= len(self.frames) - 1:
                self.frame_index = 0
            self.playing = True
            self._sync_clock()

    def set_speed(self, speed):
        # Re-sync clock so speed change doesn't cause a jump
        if self.playing:
            self._sync_clock()
        self.speed = speed

    def seek(self, fraction):
        """Seek to a fraction (0.0–1.0) of the recording."""
        fraction = max(0.0, min(1.0, fraction))
        self.frame_index = int(fraction * (len(self.frames) - 1))
        self._sync_clock()

    def skip_seconds(self, delta_s):
        """Skip forward/backward by delta_s seconds of recording time."""
        if not self.frames:
            return
        current_ts = self.frames[self.frame_index].get('timestamp', 0)
        target_ts = current_ts + delta_s * 1000  # ms

        if delta_s > 0:
            while (self.frame_index < len(self.frames) - 1 and
                   self.frames[self.frame_index].get('timestamp', 0) < target_ts):
                self.frame_index += 1
        else:
            while (self.frame_index > 0 and
                   self.frames[self.frame_index].get('timestamp', 0) > target_ts):
                self.frame_index -= 1

        self._sync_clock()

    def progress(self):
        """Return playback progress as 0.0–1.0."""
        if len(self.frames) <= 1:
            return 0.0
        return self.frame_index / (len(self.frames) - 1)

    def total_duration_s(self):
        """Total recording duration in seconds."""
        if len(self.frames) < 2:
            return 0.0
        t0 = self.frames[0].get('timestamp', 0)
        t1 = self.frames[-1].get('timestamp', 0)
        return (t1 - t0) / 1000.0

    def current_time_s(self):
        """Current playback position in seconds from start."""
        if not self.frames:
            return 0.0
        t0 = self.frames[0].get('timestamp', 0)
        tc = self.frames[self.frame_index].get('timestamp', 0)
        return (tc - t0) / 1000.0

    def frame_count(self):
        return len(self.frames)


def format_time(seconds):
    """Format seconds as MM:SS."""
    m = int(seconds) // 60
    s = int(seconds) % 60
    return f"{m:02d}:{s:02d}"


# ─── GUI Application ─────────────────────────────────────────────────────────

class TrackMapApp:
    """Tkinter application showing live track map with zoom/pan."""

    CANVAS_W = 800
    CANVAS_H = 600
    BG_COLOR = '#1a1a2e'
    TRACK_COLOR = '#4a4a6a'
    CAR_COLOR = '#ff3333'
    CAR_RADIUS = 6
    OTHER_CAR_COLOR = '#3399ff'
    OTHER_CAR_RADIUS = 4
    START_COLOR = '#ffffff'
    HUD_COLOR = '#cccccc'
    UPDATE_MS = 100  # 10 Hz
    MAX_OTHER_CARS = 21
    ZOOM_FACTOR = 1.2
    PROGRESS_BAR_H = 8
    PROGRESS_BG = '#333355'
    PROGRESS_FG = '#ff5555'

    def __init__(self, track_map, reader=None, replay_mode=False):
        self.track_map = track_map
        self.reader = reader if reader else TelemetryReader()
        self.replay_mode = replay_mode
        self.follow_player = False
        self.needs_redraw = False
        self.drag_start = None

        self.transform = CoordTransform(
            track_map['us'], track_map['vs'],
            self.CANVAS_W, self.CANVAS_H
        )

        # Build GUI
        self.root = tk.Tk()
        title = 'F1 2025 Race Replay' if replay_mode else 'F1 2025 Track Map'
        self.root.title(title)
        self.root.configure(bg=self.BG_COLOR)
        self.root.resizable(True, True)

        # Bring window to front on macOS
        self.root.lift()
        self.root.attributes('-topmost', True)
        self.root.after(100, lambda: self.root.attributes('-topmost', False))

        self.canvas = tk.Canvas(
            self.root,
            width=self.CANVAS_W,
            height=self.CANVAS_H,
            bg=self.BG_COLOR,
            highlightthickness=0
        )
        self.canvas.pack(fill=tk.BOTH, expand=True)

        # Bind events
        self.canvas.bind('<Configure>', self._on_resize)
        self.canvas.bind('<MouseWheel>', self._on_scroll)          # macOS/Windows
        self.canvas.bind('<Button-4>', self._on_scroll_up)         # Linux
        self.canvas.bind('<Button-5>', self._on_scroll_down)       # Linux
        self.canvas.bind('<ButtonPress-1>', self._on_click)
        self.canvas.bind('<B1-Motion>', self._on_drag)
        self.canvas.bind('<ButtonRelease-1>', self._on_drag_end)
        self.root.bind('<Key-r>', self._on_reset)
        self.root.bind('<Key-R>', self._on_reset)
        self.root.bind('<Key-f>', self._on_toggle_follow)
        self.root.bind('<Key-F>', self._on_toggle_follow)
        self.root.bind('<Key-plus>', self._on_zoom_in_key)
        self.root.bind('<Key-equal>', self._on_zoom_in_key)
        self.root.bind('<Key-minus>', self._on_zoom_out_key)

        # Replay-specific bindings
        if self.replay_mode:
            self.root.bind('<space>', self._on_replay_toggle)
            self.root.bind('<Left>', self._on_replay_back)
            self.root.bind('<Right>', self._on_replay_forward)
            self.root.bind('<Key-1>', lambda e: self._on_replay_speed(1.0))
            self.root.bind('<Key-2>', lambda e: self._on_replay_speed(2.0))
            self.root.bind('<Key-3>', lambda e: self._on_replay_speed(4.0))
            self.root.bind('<Key-4>', lambda e: self._on_replay_speed(0.5))

        # Initial draw
        self._full_redraw()

    def _full_redraw(self):
        """Redraw everything on canvas."""
        self.canvas.delete('all')
        self._draw_track()

        # Other car markers
        self.other_car_markers = []
        self.other_car_labels = []
        for _ in range(self.MAX_OTHER_CARS):
            marker = self.canvas.create_oval(
                -20, -20, -20, -20,
                fill=self.OTHER_CAR_COLOR, outline='#66bbff', width=1
            )
            label = self.canvas.create_text(
                -20, -20, text='', fill='#99ccff',
                font=('Courier', 8), anchor='s'
            )
            self.other_car_markers.append(marker)
            self.other_car_labels.append(label)

        # Player marker
        self.car_marker = self.canvas.create_oval(
            0, 0, 0, 0, fill=self.CAR_COLOR, outline='#ff6666', width=2
        )

        # HUD text (fixed position, not affected by zoom)
        self.hud_text = self.canvas.create_text(
            10, 10, anchor='nw', fill=self.HUD_COLOR,
            font=('Courier', 14, 'bold'), text='Waiting for telemetry...'
        )

        # Zoom info
        zoom_pct = int(self.transform.zoom * 100)
        follow_str = '  [F]ollow ON' if self.follow_player else ''
        self.zoom_text = self.canvas.create_text(
            self.CANVAS_W - 10, 10, anchor='ne', fill='#555577',
            font=('Courier', 10),
            text=f'Zoom: {zoom_pct}%{follow_str}  [R]eset  Scroll=Zoom  Drag=Pan'
        )

        # Progress bar (replay mode)
        if self.replay_mode:
            bar_y = self.CANVAS_H - 30
            self.progress_bg = self.canvas.create_rectangle(
                0, bar_y, self.CANVAS_W, bar_y + self.PROGRESS_BAR_H,
                fill=self.PROGRESS_BG, outline='', width=0
            )
            self.progress_fill = self.canvas.create_rectangle(
                0, bar_y, 0, bar_y + self.PROGRESS_BAR_H,
                fill=self.PROGRESS_FG, outline='', width=0
            )
            # Replay status text (below HUD, left side)
            self.replay_text = self.canvas.create_text(
                10, 30, anchor='nw', fill='#aaaacc',
                font=('Courier', 11),
                text=''
            )
        else:
            self.progress_bg = None
            self.progress_fill = None
            self.replay_text = None

        # Track name
        track_name = get_track_name_safe(self.track_map.get('track_id'))
        bottom_y = self.CANVAS_H - 45 if self.replay_mode else self.CANVAS_H - 15
        self.title_text = self.canvas.create_text(
            self.CANVAS_W // 2, bottom_y,
            anchor='s', fill='#666688',
            font=('Courier', 11), text=track_name
        )

        self.needs_redraw = False

    def _draw_track(self):
        """Draw the track outline as a closed polyline."""
        coords = []
        us = self.track_map['us']
        vs = self.track_map['vs']

        step = max(1, len(us) // 2000)
        for i in range(0, len(us), step):
            cx, cy = self.transform.to_canvas(us[i], vs[i])
            coords.extend([cx, cy])

        # Close the loop
        cx, cy = self.transform.to_canvas(us[0], vs[0])
        coords.extend([cx, cy])

        if len(coords) >= 4:
            # Scale track width with zoom
            track_w = max(2, int(8 * min(self.transform.zoom, 3)))
            center_w = max(1, int(2 * min(self.transform.zoom, 3)))

            self.canvas.create_line(
                *coords, fill=self.TRACK_COLOR, width=track_w,
                smooth=True, capstyle='round', joinstyle='round'
            )
            self.canvas.create_line(
                *coords, fill='#6a6a9a', width=center_w,
                smooth=True
            )

        # Start/finish marker
        sx, sy = self.transform.to_canvas(us[0], vs[0])
        r = max(3, int(4 * min(self.transform.zoom, 3)))
        self.canvas.create_oval(
            sx - r, sy - r, sx + r, sy + r,
            fill=self.START_COLOR, outline=self.START_COLOR
        )
        self.canvas.create_text(
            sx + r + 4, sy - r - 2, anchor='sw', fill=self.START_COLOR,
            font=('Courier', 9), text='S/F'
        )

    # ─── Event Handlers ───────────────────────────────────────────────────

    def _on_resize(self, event):
        new_w = event.width
        new_h = event.height
        if new_w < 200 or new_h < 150:
            return
        self.CANVAS_W = new_w
        self.CANVAS_H = new_h
        self.transform.canvas_w = new_w
        self.transform.canvas_h = new_h
        self.needs_redraw = True

    def _on_scroll(self, event):
        # macOS: event.delta is +/- 120 (or multiples)
        if event.delta > 0:
            self.transform.zoom_at(self.ZOOM_FACTOR, event.x, event.y)
        else:
            self.transform.zoom_at(1.0 / self.ZOOM_FACTOR, event.x, event.y)
        self.needs_redraw = True

    def _on_scroll_up(self, event):
        self.transform.zoom_at(self.ZOOM_FACTOR, event.x, event.y)
        self.needs_redraw = True

    def _on_scroll_down(self, event):
        self.transform.zoom_at(1.0 / self.ZOOM_FACTOR, event.x, event.y)
        self.needs_redraw = True

    def _on_click(self, event):
        # Check if click is on the progress bar (replay mode)
        if self.replay_mode and isinstance(self.reader, ReplayReader):
            bar_y = self.CANVAS_H - 30
            if bar_y <= event.y <= bar_y + self.PROGRESS_BAR_H:
                fraction = event.x / self.CANVAS_W
                self.reader.seek(fraction)
                return
        self.drag_start = (event.x, event.y)

    def _on_drag(self, event):
        if self.drag_start:
            dx = event.x - self.drag_start[0]
            dy = event.y - self.drag_start[1]
            self.transform.pan_x += dx
            self.transform.pan_y += dy
            self.drag_start = (event.x, event.y)
            self.needs_redraw = True

    def _on_drag_end(self, event):
        self.drag_start = None

    def _on_reset(self, event=None):
        self.transform.reset(self.CANVAS_W, self.CANVAS_H)
        self.follow_player = False
        self.needs_redraw = True

    def _on_toggle_follow(self, event=None):
        self.follow_player = not self.follow_player
        self.needs_redraw = True

    def _on_zoom_in_key(self, event=None):
        cx, cy = self.CANVAS_W / 2, self.CANVAS_H / 2
        self.transform.zoom_at(self.ZOOM_FACTOR, cx, cy)
        self.needs_redraw = True

    def _on_zoom_out_key(self, event=None):
        cx, cy = self.CANVAS_W / 2, self.CANVAS_H / 2
        self.transform.zoom_at(1.0 / self.ZOOM_FACTOR, cx, cy)
        self.needs_redraw = True

    # ─── Replay Controls ─────────────────────────────────────────────────

    def _on_replay_toggle(self, event=None):
        if isinstance(self.reader, ReplayReader):
            self.reader.toggle_play()

    def _on_replay_back(self, event=None):
        if isinstance(self.reader, ReplayReader):
            self.reader.skip_seconds(-5)

    def _on_replay_forward(self, event=None):
        if isinstance(self.reader, ReplayReader):
            self.reader.skip_seconds(5)

    def _on_replay_speed(self, speed):
        if isinstance(self.reader, ReplayReader):
            self.reader.set_speed(speed)

    # ─── Update Loop ─────────────────────────────────────────────────────

    def _update(self):
        """Poll telemetry and update canvas."""
        data = self.reader.get_latest()

        if data:
            player = data.get('player', {})
            lap_dist = player.get('lapDistance', 0.0)
            position = player.get('position', 0)
            lap_num = player.get('lapNumber', 0)
            speed = player.get('speed', 0)
            gear = player.get('gear', 0)
            throttle = player.get('throttle', 0.0)
            brake = player.get('brake', 0.0)

            # Follow player if enabled
            if self.follow_player:
                pu, pv = lookup_position(self.track_map, lap_dist)
                self.transform.center_on(pu, pv)
                self.needs_redraw = True

            # Redraw track if zoom/pan/resize changed
            if self.needs_redraw:
                self._full_redraw()

            # Update other cars
            all_cars = data.get('allCars', [])
            for i in range(self.MAX_OTHER_CARS):
                if i < len(all_cars):
                    car = all_cars[i]
                    car_dist = car.get('lapDistance', 0.0)
                    car_pos = car.get('position', 0)
                    cu, cv = lookup_position(self.track_map, car_dist)
                    ccx, ccy = self.transform.to_canvas(cu, cv)
                    r = self.OTHER_CAR_RADIUS
                    self.canvas.coords(
                        self.other_car_markers[i],
                        ccx - r, ccy - r, ccx + r, ccy + r
                    )
                    self.canvas.coords(
                        self.other_car_labels[i],
                        ccx, ccy - r - 2
                    )
                    self.canvas.itemconfig(
                        self.other_car_labels[i], text=f'P{car_pos}'
                    )
                else:
                    self.canvas.coords(
                        self.other_car_markers[i], -20, -20, -20, -20
                    )
                    self.canvas.coords(self.other_car_labels[i], -20, -20)
                    self.canvas.itemconfig(self.other_car_labels[i], text='')

            # Player position
            u, v = lookup_position(self.track_map, lap_dist)
            cx, cy = self.transform.to_canvas(u, v)
            r = self.CAR_RADIUS
            self.canvas.coords(self.car_marker, cx - r, cy - r, cx + r, cy + r)
            self.canvas.tag_raise(self.car_marker)

            # HUD
            n_cars = len(all_cars) + 1
            hud = f"P{position}/{n_cars}  Lap {lap_num}  {speed} km/h  G{gear}"
            hud += f"  T:{throttle:.0%}  B:{brake:.0%}"
            self.canvas.itemconfig(self.hud_text, text=hud)

            # Zoom info
            zoom_pct = int(self.transform.zoom * 100)
            follow_str = '  [F]ollow ON' if self.follow_player else ''
            if self.replay_mode:
                self.canvas.itemconfig(
                    self.zoom_text,
                    text=f'Zoom: {zoom_pct}%{follow_str}  [R]eset  Scroll=Zoom  Drag=Pan'
                )
            else:
                self.canvas.itemconfig(
                    self.zoom_text,
                    text=f'Zoom: {zoom_pct}%{follow_str}  [R]eset  Scroll=Zoom  Drag=Pan'
                )

            # Replay progress bar + status
            if self.replay_mode and isinstance(self.reader, ReplayReader):
                progress = self.reader.progress()
                bar_y = self.CANVAS_H - 30
                fill_w = progress * self.CANVAS_W
                self.canvas.coords(
                    self.progress_bg, 0, bar_y, self.CANVAS_W, bar_y + self.PROGRESS_BAR_H
                )
                self.canvas.coords(
                    self.progress_fill, 0, bar_y, fill_w, bar_y + self.PROGRESS_BAR_H
                )
                self.canvas.tag_raise(self.progress_bg)
                self.canvas.tag_raise(self.progress_fill)

                cur = format_time(self.reader.current_time_s())
                tot = format_time(self.reader.total_duration_s())
                state = "Playing" if self.reader.playing else "Paused"
                spd = self.reader.speed
                spd_str = f"{spd:.1f}x" if spd != int(spd) else f"{int(spd)}x"
                self.canvas.itemconfig(
                    self.replay_text,
                    text=f"{state}  {cur} / {tot}  [{spd_str}]  Space=Play/Pause  \u2190\u2192=\u00b15s  1-4=Speed"
                )
        else:
            # Still handle redraw even without new data (e.g. user zoomed)
            if self.needs_redraw:
                self._full_redraw()

        self.root.after(self.UPDATE_MS, self._update)

    def run(self, preview_only=False):
        """Start reader thread and tkinter mainloop."""
        if preview_only:
            self.canvas.itemconfig(self.hud_text, text='Preview mode (no live data)')
            self._schedule_redraw_check()
        elif self.replay_mode:
            self.reader.start()
            self.root.after(self.UPDATE_MS, self._update)
        else:
            self.reader.start()
            self.root.after(self.UPDATE_MS, self._update)

        try:
            self.root.mainloop()
        except KeyboardInterrupt:
            pass
        finally:
            self.reader.stop()

    def _schedule_redraw_check(self):
        """Check for needed redraws in preview mode."""
        if self.needs_redraw:
            self._full_redraw()
            self.canvas.itemconfig(self.hud_text, text='Preview mode (no live data)')
            zoom_pct = int(self.transform.zoom * 100)
            self.canvas.itemconfig(
                self.zoom_text,
                text=f'Zoom: {zoom_pct}%  [R]eset  Scroll=Zoom  Drag=Pan'
            )
        self.root.after(self.UPDATE_MS, self._schedule_redraw_check)


# ─── Track Name Helper ────────────────────────────────────────────────────────

TRACK_NAMES = {
    0: "Melbourne (Australia)", 1: "Paul Ricard (France)",
    2: "Shanghai (China)", 3: "Sakhir (Bahrain)",
    4: "Catalunya (Spain)", 5: "Monaco", 6: "Montreal (Canada)",
    7: "Silverstone (Great Britain)", 8: "Hockenheim (Germany)",
    9: "Hungaroring (Hungary)", 10: "Spa (Belgium)",
    11: "Monza (Italy)", 12: "Singapore",
    13: "Suzuka (Japan)", 14: "Abu Dhabi",
    15: "Austin (USA)", 16: "Interlagos (Brazil)",
    17: "Red Bull Ring (Austria)", 18: "Sochi (Russia)",
    19: "Mexico City", 20: "Baku (Azerbaijan)",
    21: "Sakhir Short", 22: "Silverstone Short",
    23: "Austin Short", 24: "Suzuka Short",
    25: "Hanoi (Vietnam)", 26: "Zandvoort (Netherlands)",
    27: "Imola (Italy)", 28: "Portimao (Portugal)",
    29: "Jeddah (Saudi Arabia)", 30: "Miami (USA)",
    31: "Las Vegas (USA)", 32: "Losail (Qatar)",
}


def get_track_name_safe(track_id):
    if track_id is None:
        return "Unknown Track"
    return TRACK_NAMES.get(track_id, f"Track {track_id}")


# ─── Main ────────────────────────────────────────────────────────────────────

def main():
    preview = '--preview' in sys.argv
    replay_file = None

    # Parse --replay <file>
    raw_args = sys.argv[1:]
    if '--replay' in raw_args:
        idx = raw_args.index('--replay')
        if idx + 1 < len(raw_args):
            replay_file = raw_args[idx + 1]
            raw_args = raw_args[:idx] + raw_args[idx + 2:]
        else:
            print("ERROR: --replay requires a JSONL file path")
            sys.exit(1)

    args = [a for a in raw_args if a != '--preview']

    if not args:
        print("Usage: python3 track_map_live.py <track_map.json> [options]")
        print()
        print("Options:")
        print("  --preview              Show track map only (no live data)")
        print("  --replay <file.jsonl>  Replay a recorded telemetry file")
        print()
        print("Controls:")
        print("  Scroll wheel    Zoom in/out (toward cursor)")
        print("  Click + drag    Pan the map")
        print("  +/-             Zoom in/out (center)")
        print("  R               Reset zoom to fit")
        print("  F               Follow player car (toggle)")
        print()
        print("Replay controls:")
        print("  Space           Play / pause")
        print("  Left / Right    Skip -5s / +5s")
        print("  1 / 2 / 3 / 4  Speed 1x / 2x / 4x / 0.5x")
        print("  Click bar       Seek to position")
        print()
        print("Examples:")
        print("  python3 track_map_live.py track_0_map.json --preview")
        print("  python3 track_map_live.py track_0_map.json --replay race.jsonl")
        print("  mvn -q exec:java ... 2>&1 | python3 track_map_live.py track_0_map.json")
        sys.exit(1)

    map_path = args[0]

    try:
        track_map = load_track_map(map_path)
    except FileNotFoundError:
        print(f"ERROR: Track map not found: {map_path}")
        sys.exit(1)
    except (json.JSONDecodeError, KeyError) as e:
        print(f"ERROR: Invalid track map file: {e}")
        sys.exit(1)

    print(f"Loaded track map: {track_map['num_points']} points, "
          f"{track_map['track_length']}m")

    if replay_file:
        reader = ReplayReader(replay_file)
        dur = format_time(reader.total_duration_s())
        print(f"Replay: {reader.frame_count()} frames, {dur} duration")
        print("Controls: Space=Play/Pause | Left/Right=Skip | 1-4=Speed | Scroll=Zoom | Drag=Pan")
        app = TrackMapApp(track_map, reader=reader, replay_mode=True)
        app.run()
    elif preview:
        print("Opening preview... (close window to exit)")
        print("Controls: Scroll=Zoom | Drag=Pan | R=Reset | +/-=Zoom")
        app = TrackMapApp(track_map)
        app.run(preview_only=True)
    else:
        print("Starting GUI... (close window or Ctrl+C to stop)")
        print("Controls: Scroll=Zoom | Drag=Pan | R=Reset | F=Follow | +/-=Zoom")
        app = TrackMapApp(track_map)
        app.run()


if __name__ == '__main__':
    main()
