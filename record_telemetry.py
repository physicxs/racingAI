#!/usr/bin/env python3
"""
Records F1 2025 telemetry to a JSONL file.
Shows live statistics while recording.
"""

import json
import sys
import time
from datetime import datetime

def format_duration(seconds):
    """Format duration as MM:SS"""
    mins = int(seconds // 60)
    secs = int(seconds % 60)
    return f"{mins:02d}:{secs:02d}"

# Generate filename with timestamp
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
filename = f"telemetry_{timestamp}.jsonl"

print(f"╔════════════════════════════════════════════════════════════════════════════════╗")
print(f"║ F1 2025 TELEMETRY RECORDER                                                     ║")
print(f"╚════════════════════════════════════════════════════════════════════════════════╝")
print()
print(f"Recording to: {filename}")
print()
print("Waiting for telemetry data...")
print()

frame_count = 0
session_packets = 0
start_time = None
last_update_time = time.time()
track_name = "Unknown"
position = 0
lap_number = 0
speed = 0

with open(filename, 'w') as f:
    for line in sys.stdin:
        # Pass through log messages to stderr
        if not line.startswith('{'):
            print(line.rstrip(), file=sys.stderr)
            sys.stderr.flush()
            continue

        try:
            # Write to file
            f.write(line)
            f.flush()  # Ensure data is written immediately

            # Parse for statistics
            data = json.loads(line.strip())
            frame_count += 1

            if start_time is None:
                start_time = time.time()
                print("✓ Recording started!\n")

            # Extract data for display
            meta = data.get('meta', {})
            player = data.get('player', {})

            track_id = meta.get('track_id')
            if track_id is not None and track_id != 0:
                # Track ID mapping (simplified)
                track_names = {
                    0: "Melbourne", 1: "Paul Ricard", 2: "Shanghai", 3: "Sakhir",
                    5: "Monaco", 7: "Silverstone", 10: "Spa", 11: "Monza",
                    12: "Singapore", 13: "Suzuka", 29: "Jeddah", 30: "Miami",
                    31: "Las Vegas"
                }
                track_name = track_names.get(track_id, f"Track {track_id}")

            position = player.get('position', 0)
            lap_number = player.get('lapNumber', 0)
            speed = player.get('speed', 0)

            # Update display every second
            current_time = time.time()
            if current_time - last_update_time >= 1.0:
                duration = current_time - start_time if start_time else 0
                hz = frame_count / duration if duration > 0 else 0

                # Clear previous lines and redraw
                print('\033[3A\033[J', end='')  # Move up 3 lines and clear

                print(f"Recording: {format_duration(duration)} │ Frames: {frame_count:,} │ Rate: {hz:.1f} Hz")
                print(f"Track: {track_name} │ P{position} │ Lap {lap_number} │ {speed} km/h")
                print()

                last_update_time = current_time

        except json.JSONDecodeError:
            pass
        except KeyboardInterrupt:
            break

# Summary
if start_time:
    duration = time.time() - start_time
    avg_hz = frame_count / duration if duration > 0 else 0

    print("\n" + "="*80)
    print("RECORDING COMPLETE")
    print("="*80)
    print(f"File:           {filename}")
    print(f"Duration:       {format_duration(duration)}")
    print(f"Frames:         {frame_count:,}")
    print(f"Average rate:   {avg_hz:.1f} Hz")
    print(f"Track:          {track_name}")
    print(f"Final position: P{position}")
    print(f"Laps recorded:  {lap_number}")
    print("="*80)
else:
    print("\nNo data received")
