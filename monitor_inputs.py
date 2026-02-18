#!/usr/bin/env python3
"""
Live input monitor for F1 telemetry.
Displays steering, throttle, brake, clutch, gear, and speed at 10 Hz.
"""

import json
import sys
import time

def format_bar(value, width=20, char='█'):
    """Create a visual bar for 0-1 values"""
    filled = int(value * width)
    return char * filled + '░' * (width - filled)

def format_steer_bar(value, width=40):
    """Create a centered steering bar (-1 to +1)"""
    center = width // 2
    if value < 0:  # Left
        filled = int(abs(value) * center)
        left_part = '░' * (center - filled) + '◄' * filled
        right_part = '░' * center
    else:  # Right
        filled = int(value * center)
        left_part = '░' * center
        right_part = '►' * filled + '░' * (center - filled)
    return left_part + '|' + right_part

frame_count = 0
last_time = time.time()
data_received = False

try:
    for line in sys.stdin:
        # Pass through log messages
        if not line.startswith('{'):
            print(line.rstrip())
            sys.stdout.flush()
            continue

        try:
            data = json.loads(line.strip())
            player = data.get('player', {})

            # Extract values
            steer = player.get('steering', 0.0)
            throttle = player.get('throttle', 0.0)
            brake = player.get('brake', 0.0)
            clutch = player.get('clutch', 0.0) if 'clutch' in player else 0.0
            gear = player.get('gear', 0)
            speed = player.get('speed', 0)

            # Display at ~10 Hz (every 3rd frame from 30 Hz input)
            frame_count += 1
            if frame_count % 3 == 0:
                if not data_received:
                    data_received = True
                    print("\n✓ Receiving telemetry data!\n")

                current_time = time.time()
                hz = 1.0 / (current_time - last_time) if (current_time - last_time) > 0 else 0
                last_time = current_time

                # Clear screen and display
                print('\033[H\033[J', end='')  # Clear screen
                print(f"Live Input Monitor - {hz:.1f} Hz")
                print("=" * 80)
                print()

                # Steering (centered bar)
                print(f"Steer:    {format_steer_bar(steer)} [{steer:+.4f}]")
                print(f"          {'LEFT' if steer < -0.05 else '    '}    {'RIGHT' if steer > 0.05 else '     '}")
                print()

                # Throttle
                print(f"Throttle: {format_bar(throttle)} [{throttle:.3f}]")

                # Brake
                print(f"Brake:    {format_bar(brake)} [{brake:.3f}]")

                # Clutch (if available)
                if 'clutch' in player:
                    print(f"Clutch:   {format_bar(clutch)} [{clutch:.3f}]")

                print()

                # Gear and Speed
                print(f"Gear:     {gear}")
                print(f"Speed:    {speed} km/h")
                print()
                print("Turn your wheel to test steering response...")
                print("Press Ctrl+C to stop")

                sys.stdout.flush()

        except json.JSONDecodeError:
            pass

except KeyboardInterrupt:
    print("\n\n✓ Monitor stopped")
    sys.exit(0)
