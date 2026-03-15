#!/usr/bin/env python3
"""
F1 2025 Live Track Map GUI

Displays a real-time track map with the player car's position.
Reads a pre-built track map JSON and live telemetry from stdin.

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


# ─── Coordinate Transform ────────────────────────────────────────────────────

class CoordTransform:
    """Maps track (u, v) coordinates to canvas pixel coordinates."""

    def __init__(self, us, vs, canvas_w, canvas_h, margin=50):
        min_u, max_u = min(us), max(us)
        min_v, max_v = min(vs), max(vs)

        range_u = max_u - min_u or 1.0
        range_v = max_v - min_v or 1.0

        scale_u = (canvas_w - 2 * margin) / range_u
        scale_v = (canvas_h - 2 * margin) / range_v
        self.scale = min(scale_u, scale_v)

        # Center the track in the canvas
        scaled_w = range_u * self.scale
        scaled_h = range_v * self.scale
        self.offset_x = (canvas_w - scaled_w) / 2
        self.offset_y = (canvas_h - scaled_h) / 2

        self.min_u = min_u
        self.min_v = min_v

    def to_canvas(self, u, v):
        """Convert track (u, v) to canvas (x, y)."""
        cx = (u - self.min_u) * self.scale + self.offset_x
        cy = (v - self.min_v) * self.scale + self.offset_y
        return cx, cy


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
    """Tkinter application showing live track map."""

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

    def __init__(self, track_map):
        self.track_map = track_map
        self.reader = TelemetryReader()
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

        # Handle window resize
        self.canvas.bind('<Configure>', self._on_resize)

        # Draw track
        self._draw_track()

        # Create other car markers (drawn first so player is on top)
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

        # Create player car marker (on top of others)
        self.car_marker = self.canvas.create_oval(
            0, 0, 0, 0, fill=self.CAR_COLOR, outline='#ff6666', width=2
        )

        # HUD text
        self.hud_text = self.canvas.create_text(
            10, 10, anchor='nw', fill=self.HUD_COLOR,
            font=('Courier', 14, 'bold'), text='Waiting for telemetry...'
        )

        # Track name
        track_name = get_track_name_safe(track_map.get('track_id'))
        self.title_text = self.canvas.create_text(
            self.CANVAS_W // 2, self.CANVAS_H - 15,
            anchor='s', fill='#666688',
            font=('Courier', 11), text=track_name
        )

    def _draw_track(self):
        """Draw the track outline as a closed polyline."""
        coords = []
        us = self.track_map['us']
        vs = self.track_map['vs']

        # Sample every few meters to avoid too many points
        step = max(1, len(us) // 2000)
        for i in range(0, len(us), step):
            cx, cy = self.transform.to_canvas(us[i], vs[i])
            coords.extend([cx, cy])

        # Close the loop
        cx, cy = self.transform.to_canvas(us[0], vs[0])
        coords.extend([cx, cy])

        if len(coords) >= 4:
            self.track_line = self.canvas.create_line(
                *coords, fill=self.TRACK_COLOR, width=8,
                smooth=True, capstyle='round', joinstyle='round'
            )
            # Draw a thinner bright center line
            self.track_center = self.canvas.create_line(
                *coords, fill='#6a6a9a', width=2,
                smooth=True
            )

        # Start/finish marker
        sx, sy = self.transform.to_canvas(us[0], vs[0])
        self.canvas.create_oval(
            sx - 4, sy - 4, sx + 4, sy + 4,
            fill=self.START_COLOR, outline=self.START_COLOR
        )
        self.canvas.create_text(
            sx + 10, sy - 10, anchor='sw', fill=self.START_COLOR,
            font=('Courier', 9), text='S/F'
        )

    def _on_resize(self, event):
        """Handle window resize by recalculating transform and redrawing."""
        new_w = event.width
        new_h = event.height
        if new_w < 200 or new_h < 150:
            return

        self.CANVAS_W = new_w
        self.CANVAS_H = new_h
        self.transform = CoordTransform(
            self.track_map['us'], self.track_map['vs'],
            new_w, new_h
        )

        # Redraw everything
        self.canvas.delete('all')
        self._draw_track()
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
        self.car_marker = self.canvas.create_oval(
            0, 0, 0, 0, fill=self.CAR_COLOR, outline='#ff6666', width=2
        )
        self.hud_text = self.canvas.create_text(
            10, 10, anchor='nw', fill=self.HUD_COLOR,
            font=('Courier', 14, 'bold'), text='Waiting for telemetry...'
        )
        track_name = get_track_name_safe(self.track_map.get('track_id'))
        self.title_text = self.canvas.create_text(
            new_w // 2, new_h - 15,
            anchor='s', fill='#666688',
            font=('Courier', 11), text=track_name
        )

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

            # Update other cars from allCars array
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
                    # Hide unused markers
                    self.canvas.coords(
                        self.other_car_markers[i], -20, -20, -20, -20
                    )
                    self.canvas.coords(
                        self.other_car_labels[i], -20, -20
                    )
                    self.canvas.itemconfig(self.other_car_labels[i], text='')

            # Look up player position on track map
            u, v = lookup_position(self.track_map, lap_dist)
            cx, cy = self.transform.to_canvas(u, v)

            # Move player car marker (always on top)
            r = self.CAR_RADIUS
            self.canvas.coords(self.car_marker, cx - r, cy - r, cx + r, cy + r)
            self.canvas.tag_raise(self.car_marker)

            # Update HUD
            n_cars = len(all_cars) + 1
            hud = f"P{position}/{n_cars}  Lap {lap_num}  {speed} km/h  G{gear}"
            hud += f"  T:{throttle:.0%}  B:{brake:.0%}"
            self.canvas.itemconfig(self.hud_text, text=hud)

        # Schedule next update
        self.root.after(self.UPDATE_MS, self._update)

    def run(self, preview_only=False):
        """Start reader thread and tkinter mainloop."""
        if not preview_only:
            self.reader.start()
            self.root.after(self.UPDATE_MS, self._update)
        else:
            self.canvas.itemconfig(self.hud_text, text='Preview mode (no live data)')

        try:
            self.root.mainloop()
        except KeyboardInterrupt:
            pass
        finally:
            self.reader.stop()


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

    app = TrackMapApp(track_map)
    app.run(preview_only=preview)


if __name__ == '__main__':
    main()
