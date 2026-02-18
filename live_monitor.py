#!/usr/bin/env python3
"""
Comprehensive live telemetry monitor for F1 2025.
Shows track, position, inputs, and nearby cars at 10 Hz.
"""

import json
import sys
import time

# Track ID mapping
TRACK_NAMES = {
    -1: "Unknown",
    0: "Melbourne (Australia)",
    1: "Paul Ricard (France)",
    2: "Shanghai (China)",
    3: "Sakhir (Bahrain)",
    4: "Catalunya (Spain)",
    5: "Monaco",
    6: "Montreal (Canada)",
    7: "Silverstone (Great Britain)",
    8: "Hockenheim (Germany)",
    9: "Hungaroring (Hungary)",
    10: "Spa (Belgium)",
    11: "Monza (Italy)",
    12: "Singapore",
    13: "Suzuka (Japan)",
    14: "Abu Dhabi (UAE)",
    15: "Texas (USA)",
    16: "Brazil",
    17: "Austria",
    18: "Sochi (Russia)",
    19: "Mexico",
    20: "Baku (Azerbaijan)",
    21: "Sakhir Short",
    22: "Silverstone Short",
    23: "Texas Short",
    24: "Suzuka Short",
    25: "Hanoi (Vietnam)",
    26: "Zandvoort (Netherlands)",
    27: "Imola (Italy)",
    28: "Portimão (Portugal)",
    29: "Jeddah (Saudi Arabia)",
    30: "Miami (USA)",
    31: "Las Vegas (USA)",
    32: "Losail (Qatar)"
}

def get_track_name(track_id):
    """Get track name from ID"""
    return TRACK_NAMES.get(track_id, f"Unknown Track (ID: {track_id})")

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

            # Extract data
            meta = data.get('meta', {})
            player = data.get('player', {})
            nearby_cars = data.get('nearbyCars', [])

            track_id = meta.get('track_id')
            track_name = get_track_name(track_id) if track_id is not None else "Not Set"

            position = player.get('position', 0)
            lap_number = player.get('lapNumber', 0)
            lap_distance = player.get('lapDistance', 0.0)

            steer = player.get('steering', 0.0)
            throttle = player.get('throttle', 0.0)
            brake = player.get('brake', 0.0)
            gear = player.get('gear', 0)
            speed = player.get('speed', 0)

            tyre_wear = player.get('tyreWear', {})

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
                print("╔════════════════════════════════════════════════════════════════════════════════╗")
                print(f"║ F1 2025 LIVE TELEMETRY MONITOR{' ' * 47}║")
                print(f"║ {hz:4.1f} Hz{' ' * 71}║")
                print("╠════════════════════════════════════════════════════════════════════════════════╣")

                # Track and Session Info
                print(f"║ TRACK: {track_name:<68} ║")
                print(f"║ Position: P{position:<2}  │  Lap: {lap_number:<2}  │  Distance: {lap_distance:>7.1f}m{' ' * 31}║")
                print("╠════════════════════════════════════════════════════════════════════════════════╣")

                # Inputs
                print("║ INPUTS                                                                         ║")
                steer_label = "LEFT " if steer < -0.05 else ("RIGHT" if steer > 0.05 else "     ")
                print(f"║   Steer:    {format_steer_bar(steer)} [{steer:+.3f}] {steer_label} ║")
                print(f"║   Throttle: {format_bar(throttle)} [{throttle:.3f}]{' ' * 33}║")
                print(f"║   Brake:    {format_bar(brake)} [{brake:.3f}]{' ' * 33}║")
                print("║                                                                                ║")
                print(f"║   Gear: {gear:<2}  │  Speed: {speed:>3} km/h{' ' * 50}║")

                # Tyre Wear
                if tyre_wear:
                    fl = tyre_wear.get('frontLeft', 0.0)
                    fr = tyre_wear.get('frontRight', 0.0)
                    rl = tyre_wear.get('rearLeft', 0.0)
                    rr = tyre_wear.get('rearRight', 0.0)
                    print("╠════════════════════════════════════════════════════════════════════════════════╣")
                    print("║ TYRE WEAR                                                                      ║")
                    print(f"║   FL: {fl:5.1f}%  │  FR: {fr:5.1f}%{' ' * 52}║")
                    print(f"║   RL: {rl:5.1f}%  │  RR: {rr:5.1f}%{' ' * 52}║")

                # Nearby Cars
                if nearby_cars:
                    # Filter out invalid cars (same position as player, 0 gap, likely duplicates)
                    valid_cars = []
                    for car in nearby_cars[:6]:
                        car_pos = car.get('position', 0)
                        gap = car.get('gap', 0.0)
                        # Skip if: same position as player AND gap is 0 (likely duplicate/invalid)
                        if car_pos == position and abs(gap) < 0.01:
                            continue
                        # Skip if position is 0 or invalid
                        if car_pos == 0:
                            continue
                        valid_cars.append(car)

                    if valid_cars:
                        print("╠════════════════════════════════════════════════════════════════════════════════╣")
                        print("║ NEARBY CARS                                                                    ║")
                        for car in valid_cars:
                            car_pos = car.get('position', 0)
                            gap = car.get('gap', 0.0)
                            direction = "ahead " if car_pos < position else "behind"
                            gap_sign = "-" if car_pos < position else "+"
                            print(f"║   P{car_pos:<2} ({direction}): {gap_sign}{abs(gap):.2f}s{' ' * 56}║")

                print("╚════════════════════════════════════════════════════════════════════════════════╝")
                print("\nPress Ctrl+C to stop")

                sys.stdout.flush()

        except json.JSONDecodeError:
            pass

except KeyboardInterrupt:
    print("\n\n✓ Monitor stopped")
    sys.exit(0)
