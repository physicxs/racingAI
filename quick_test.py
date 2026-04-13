#!/usr/bin/env python3
"""Quick test to show a few frames of input data"""

import json
import subprocess
import sys
import time

print("Starting telemetry receiver...")
print("Showing first 30 frames of input data...")
print("=" * 80)
print()

# Start the Python receiver
proc = subprocess.Popen(
    ["python3", "-u", "f1_receiver.py"],
    stdout=subprocess.PIPE,
    stderr=subprocess.DEVNULL,
    text=True,
    bufsize=1
)

frame_count = 0
display_count = 0

try:
    for line in proc.stdout:
        if line.startswith('{'):
            try:
                data = json.loads(line.strip())
                player = data.get('player', {})

                frame_count += 1

                # Display every 3rd frame (10 Hz from 30 Hz)
                if frame_count % 3 == 0:
                    display_count += 1

                    steer = player.get('steering', 0.0)
                    throttle = player.get('throttle', 0.0)
                    brake = player.get('brake', 0.0)
                    gear = player.get('gear', 0)
                    speed = player.get('speed', 0)

                    # Simple display
                    print(f"[{display_count:3d}] Steer: {steer:+.4f} | Throttle: {throttle:.2f} | Brake: {brake:.2f} | Gear: {gear} | Speed: {speed:3d} km/h")

                    # Show first 30 displays
                    if display_count >= 30:
                        break

            except json.JSONDecodeError:
                pass
except KeyboardInterrupt:
    pass
finally:
    proc.terminate()
    proc.wait()

print()
print("=" * 80)
print(f"Steering sign check:")
print(f"  - Negative values = turning LEFT")
print(f"  - Positive values = turning RIGHT")
print()
print("If steering sign is inverted in your game:")
print("  Flip it in: src/main/java/com/racingai/f1telemetry/state/CarState.java")
print("  In the setSteer() method, change to: this.steer = -steer;")
