#!/usr/bin/env python3
"""
F1 2025 Live Track Map GUI

Displays a real-time track map with the player car's position.
Reads a pre-built track map JSON and live telemetry from stdin.

Controls:
    Scroll wheel    Zoom in/out
    Click + drag    Pan the map
    R               Reset zoom to fit
    F               Follow player car (toggle)
    +/-             Zoom in/out

Usage:
    mvn -q exec:java -Dexec.mainClass="..." 2>&1 | python3 track_map_live.py <track_map.json>
"""

import json
import sys
import math
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

    def __init__(self, track_map):
        self.track_map = track_map
        self.reader = TelemetryReader()
        self.follow_player = False
        self.needs_redraw = False
        self.drag_start = None

        self.transform = CoordTransform(
            track_map['us'], track_map['vs'],
            self.CANVAS_W, self.CANVAS_H
        )

        # Build GUI
        self.root = tk.Tk()
        self.root.title('F1 2025 Track Map')
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
        self.canvas.bind('<ButtonPress-1>', self._on_drag_start)
        self.canvas.bind('<B1-Motion>', self._on_drag)
        self.canvas.bind('<ButtonRelease-1>', self._on_drag_end)
        self.root.bind('<Key-r>', self._on_reset)
        self.root.bind('<Key-R>', self._on_reset)
        self.root.bind('<Key-f>', self._on_toggle_follow)
        self.root.bind('<Key-F>', self._on_toggle_follow)
        self.root.bind('<Key-plus>', self._on_zoom_in_key)
        self.root.bind('<Key-equal>', self._on_zoom_in_key)
        self.root.bind('<Key-minus>', self._on_zoom_out_key)

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

        # Track name
        track_name = get_track_name_safe(self.track_map.get('track_id'))
        self.title_text = self.canvas.create_text(
            self.CANVAS_W // 2, self.CANVAS_H - 15,
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

    def _on_drag_start(self, event):
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
            self.canvas.itemconfig(
                self.zoom_text,
                text=f'Zoom: {zoom_pct}%{follow_str}  [R]eset  Scroll=Zoom  Drag=Pan'
            )
        else:
            # Still handle redraw even without new data (e.g. user zoomed)
            if self.needs_redraw:
                self._full_redraw()

        self.root.after(self.UPDATE_MS, self._update)

    def run(self, preview_only=False):
        """Start reader thread and tkinter mainloop."""
        if not preview_only:
            self.reader.start()
            self.root.after(self.UPDATE_MS, self._update)
        else:
            self.canvas.itemconfig(self.hud_text, text='Preview mode (no live data)')
            # Still handle zoom/pan in preview mode
            self._schedule_redraw_check()

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
    args = [a for a in sys.argv[1:] if a != '--preview']

    if not args:
        print("Usage: python3 track_map_live.py <track_map.json> [--preview]")
        print()
        print("Show a real-time track map with live car position.")
        print("  --preview  Show track map only (no live telemetry needed)")
        print()
        print("Controls:")
        print("  Scroll wheel    Zoom in/out (toward cursor)")
        print("  Click + drag    Pan the map")
        print("  +/-             Zoom in/out (center)")
        print("  R               Reset zoom to fit")
        print("  F               Follow player car (toggle)")
        print()
        print("Examples:")
        print("  python3 track_map_live.py track_0_map.json --preview")
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

    if preview:
        print("Opening preview... (close window to exit)")
    else:
        print("Starting GUI... (close window or Ctrl+C to stop)")

    print("Controls: Scroll=Zoom | Drag=Pan | R=Reset | F=Follow | +/-=Zoom")

    app = TrackMapApp(track_map)
    app.run(preview_only=preview)


if __name__ == '__main__':
    main()
