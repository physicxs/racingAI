#!/usr/bin/env python3
"""
Compare Java vs Python telemetry output frame-by-frame.

Usage:
    python3 compare_outputs.py <java.jsonl> <python.jsonl>

Compares key fields and reports mismatches.
"""

import json
import sys
import math


FLOAT_TOLERANCE = 0.01
POSITION_TOLERANCE = 0.5  # meters


def compare_frames(java, python, frame_num):
    """Compare two frames, return list of mismatches."""
    mismatches = []

    jp = java.get('player', {})
    pp = python.get('player', {})

    # Integer fields (exact match)
    for key in ['speed', 'gear', 'position', 'lapNumber', 'drs', 'drsAllowed']:
        jv = jp.get(key)
        pv = pp.get(key)
        if jv != pv:
            mismatches.append(f"  player.{key}: java={jv} python={pv}")

    # Float fields (tolerance)
    for key in ['throttle', 'brake', 'steering', 'lapDistance', 'yaw', 'pitch', 'roll',
                'gForceLateral', 'gForceLongitudinal']:
        jv = jp.get(key, 0)
        pv = pp.get(key, 0)
        if jv is None or pv is None:
            continue
        if abs(jv - pv) > FLOAT_TOLERANCE:
            mismatches.append(f"  player.{key}: java={jv} python={pv} delta={abs(jv-pv):.4f}")

    # World position (tolerance)
    jwp = jp.get('world_pos_m', {})
    pwp = pp.get('world_pos_m', {})
    for axis in ['x', 'y', 'z']:
        jv = jwp.get(axis, 0)
        pv = pwp.get(axis, 0)
        if abs(jv - pv) > POSITION_TOLERANCE:
            mismatches.append(f"  player.world_pos_m.{axis}: java={jv:.2f} python={pv:.2f} delta={abs(jv-pv):.2f}")

    # Nearby cars count
    jnc = len(java.get('nearbyCars', []))
    pnc = len(python.get('nearbyCars', []))
    if jnc != pnc:
        mismatches.append(f"  nearbyCars count: java={jnc} python={pnc}")

    # All cars count
    jac = len(java.get('allCars', []))
    pac = len(python.get('allCars', []))
    if jac != pac:
        mismatches.append(f"  allCars count: java={jac} python={pac}")

    # Compare allCars positions
    j_cars = {c['carIndex']: c for c in java.get('allCars', [])}
    p_cars = {c['carIndex']: c for c in python.get('allCars', [])}
    for cid in j_cars:
        if cid not in p_cars:
            mismatches.append(f"  allCars[{cid}]: in java but not python")
            continue
        jc = j_cars[cid]
        pc = p_cars[cid]
        if jc.get('position') != pc.get('position'):
            mismatches.append(f"  allCars[{cid}].position: java={jc['position']} python={pc['position']}")
        jwp = jc.get('world_pos_m', {})
        pwp = pc.get('world_pos_m', {})
        for axis in ['x', 'z']:
            jv = jwp.get(axis, 0)
            pv = pwp.get(axis, 0)
            if abs(jv - pv) > POSITION_TOLERANCE:
                mismatches.append(f"  allCars[{cid}].{axis}: java={jv:.1f} python={pv:.1f} delta={abs(jv-pv):.1f}")

    return mismatches


def main():
    if len(sys.argv) < 3:
        print("Usage: python3 compare_outputs.py <java.jsonl> <python.jsonl>")
        sys.exit(1)

    java_path = sys.argv[1]
    python_path = sys.argv[2]

    print(f"Comparing: {java_path} vs {python_path}")

    java_frames = []
    python_frames = []

    with open(java_path) as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    java_frames.append(json.loads(line))
                except json.JSONDecodeError:
                    continue

    with open(python_path) as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    python_frames.append(json.loads(line))
                except json.JSONDecodeError:
                    continue

    print(f"  Java frames:   {len(java_frames)}")
    print(f"  Python frames: {len(python_frames)}")

    # Compare min(java, python) frames
    n = min(len(java_frames), len(python_frames))
    total_mismatches = 0
    frames_with_errors = 0
    first_errors = []

    for i in range(n):
        mismatches = compare_frames(java_frames[i], python_frames[i], i)
        if mismatches:
            frames_with_errors += 1
            total_mismatches += len(mismatches)
            if len(first_errors) < 30:
                first_errors.append((i, mismatches))

    print(f"\nResults ({n} frames compared):")
    print(f"  Frames with mismatches: {frames_with_errors} / {n} ({frames_with_errors/n*100:.1f}%)")
    print(f"  Total mismatches: {total_mismatches}")

    if first_errors:
        print(f"\nFirst mismatches:")
        for frame_num, mismatches in first_errors[:10]:
            print(f"  Frame {frame_num}:")
            for m in mismatches[:5]:
                print(f"    {m}")
    else:
        print("\nPASS: All frames match within tolerance")


if __name__ == '__main__':
    main()
