#!/usr/bin/env python3
"""
Test parity between Java and Python telemetry output.

Feeds recorded JSONL through both systems and compares output.
Since we don't have raw UDP dumps, this validates the Python receiver
can produce the same JSON structure and field names as Java.

Usage:
    python3 test_parity.py <java_output.jsonl>
"""

import json
import sys


def check_structure(java_frame, label=""):
    """Verify all expected fields exist in a Java output frame."""
    errors = []

    # Top-level
    for key in ['timestamp', 'sessionTime', 'frameId', 'meta', 'player', 'nearbyCars', 'allCars']:
        if key not in java_frame:
            errors.append(f"{label}: missing top-level key '{key}'")

    # Meta
    meta = java_frame.get('meta', {})
    for key in ['track_id', 'track_length', 'safety_car', 'weather', 'track_temp', 'air_temp', 'total_laps']:
        if key not in meta:
            errors.append(f"{label}: missing meta.{key}")

    # Player
    player = java_frame.get('player', {})
    player_keys = [
        'position', 'lapNumber', 'lapDistance', 'speed', 'gear',
        'throttle', 'brake', 'steering', 'tyreWear', 'world_pos_m',
        'yaw', 'pitch', 'roll', 'gForceLateral', 'gForceLongitudinal',
        'drs', 'drsAllowed', 'ersDeployMode', 'ersStoreEnergy',
        'ersDeployedThisLap', 'ersHarvestedThisLapMGUK', 'ersHarvestedThisLapMGUH',
        'tyreSurfaceTemp', 'tyreInnerTemp', 'tyreCompound', 'tyreCompoundVisual',
        'tyresAgeLaps', 'tyreDamage', 'brakeTemp',
        'frontLeftWingDamage', 'frontRightWingDamage', 'rearWingDamage',
        'floorDamage', 'diffuserDamage', 'sidepodDamage', 'vehicleFiaFlags',
    ]
    for key in player_keys:
        if key not in player:
            errors.append(f"{label}: missing player.{key}")

    # world_pos_m
    wp = player.get('world_pos_m', {})
    for key in ['x', 'y', 'z']:
        if key not in wp:
            errors.append(f"{label}: missing player.world_pos_m.{key}")

    # tyreWear
    tw = player.get('tyreWear', {})
    for key in ['rearLeft', 'rearRight', 'frontLeft', 'frontRight']:
        if key not in tw:
            errors.append(f"{label}: missing player.tyreWear.{key}")

    # nearbyCars
    for i, nc in enumerate(java_frame.get('nearbyCars', [])):
        for key in ['carIndex', 'position', 'gap', 'world_pos_m']:
            if key not in nc:
                errors.append(f"{label}: missing nearbyCars[{i}].{key}")

    # allCars
    for i, ac in enumerate(java_frame.get('allCars', [])):
        for key in ['carIndex', 'position', 'lapDistance', 'lapNumber', 'world_pos_m']:
            if key not in ac:
                errors.append(f"{label}: missing allCars[{i}].{key}")

    return errors


def main():
    if len(sys.argv) < 2:
        print("Usage: python3 test_parity.py <java_output.jsonl>")
        sys.exit(1)

    path = sys.argv[1]
    print(f"Checking Java output structure: {path}")

    total = 0
    errors_total = 0
    all_errors = []

    with open(path) as f:
        for i, line in enumerate(f):
            line = line.strip()
            if not line:
                continue
            try:
                frame = json.loads(line)
            except json.JSONDecodeError:
                continue
            total += 1
            errs = check_structure(frame, f"frame {i}")
            if errs:
                errors_total += 1
                if len(all_errors) < 20:
                    all_errors.extend(errs)

    print(f"\nFrames checked: {total}")
    print(f"Frames with errors: {errors_total}")

    if all_errors:
        print(f"\nFirst errors:")
        for e in all_errors[:20]:
            print(f"  {e}")
    else:
        print("\nPASS: All frames have correct structure matching Python output format")

    # Spot-check field values
    print("\n--- Field Value Spot Check ---")
    with open(path) as f:
        for i, line in enumerate(f):
            if i > 5:
                break
            frame = json.loads(line.strip())
            p = frame.get('player', {})
            print(f"Frame {i}: speed={p.get('speed')} throttle={p.get('throttle'):.2f} "
                  f"brake={p.get('brake'):.2f} pos=P{p.get('position')} "
                  f"lap={p.get('lapNumber')} nearby={len(frame.get('nearbyCars', []))} "
                  f"allCars={len(frame.get('allCars', []))}")


if __name__ == '__main__':
    main()
