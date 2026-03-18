#!/usr/bin/env python3
"""
F1 2025 Track Intelligence Builder

Converts a spline-based track map into a per-point intelligence layer
with curvature, corner detection, corner phase, and target speed.

This is a deterministic system (no ML) that provides the foundation
for driver evaluation, racecraft AI, and coaching.

Usage:
    python3 track_intelligence.py <track_map.json> [-o output.json]
"""

import json
import sys
import os
import math


# ─── Tunable Parameters ─────────────────────────────────────────────────────

MU = 1.8                    # Tire grip coefficient (1.6-2.0 for F1)
G = 9.81                    # Gravity (m/s²)
MAX_SPEED_MS = 100.0        # Speed cap (360 km/h)
CURVATURE_THRESHOLD = 0.005 # |curvature| above this = corner
CURVATURE_SMOOTH_WINDOW = 25 # Smoothing window for curvature
CURVATURE_MAX = 0.05        # Max realistic curvature (radius 20m)
SPEED_SMOOTH_WINDOW = 20    # Smoothing window for target speed
A_MAX_BRAKE = 14.0          # Max braking deceleration (m/s²)
MIN_CORNER_POINTS = 15      # Minimum points to count as a corner segment


# ─── Helpers ─────────────────────────────────────────────────────────────────

def smooth_values(values, window=10):
    """Circular moving average smoothing."""
    n = len(values)
    smoothed = [0.0] * n
    hw = window // 2
    for i in range(n):
        total = 0.0
        count = 0
        for j in range(-hw, hw + 1):
            idx = (i + j) % n
            total += values[idx]
            count += 1
        smoothed[i] = total / count
    return smoothed


def normalize_angle(a):
    """Normalize angle to [-pi, pi]."""
    while a > math.pi:
        a -= 2 * math.pi
    while a < -math.pi:
        a += 2 * math.pi
    return a


# ─── Step 1: Arc Length ──────────────────────────────────────────────────────

def compute_arc_length(us, vs):
    """Compute cumulative arc length per point."""
    n = len(us)
    s = [0.0] * n
    for i in range(1, n):
        du = us[i] - us[i - 1]
        dv = vs[i] - vs[i - 1]
        s[i] = s[i - 1] + math.sqrt(du * du + dv * dv)
    return s


# ─── Step 2: Heading ────────────────────────────────────────────────────────

def compute_heading(us, vs):
    """Compute heading angle (radians) at each point."""
    n = len(us)
    heading = [0.0] * n
    for i in range(n):
        i_next = (i + 1) % n
        du = us[i_next] - us[i]
        dv = vs[i_next] - vs[i]
        heading[i] = math.atan2(dv, du)
    return heading


# ─── Step 3: Curvature ──────────────────────────────────────────────────────

def compute_curvature(heading, arc_length):
    """Compute curvature (1/m) = dtheta/ds at each point."""
    n = len(heading)
    curvature = [0.0] * n
    for i in range(n):
        i_next = (i + 1) % n
        dtheta = normalize_angle(heading[i_next] - heading[i])
        ds = arc_length[i_next] - arc_length[i]
        if i_next == 0:
            # Wrap: estimate ds from last segment
            du = 0  # skip wrap point
            ds = 1.0  # fallback
        if abs(ds) < 0.001:
            curvature[i] = curvature[i - 1] if i > 0 else 0.0
        else:
            curvature[i] = dtheta / ds
    return curvature


# ─── Step 4: Corner Detection ───────────────────────────────────────────────

def detect_corners(curvature):
    """Label each point as corner or straight, group into corner segments.

    Returns (corner_ids, is_corner) where corner_ids[i] = -1 for straights.
    """
    n = len(curvature)
    is_corner = [abs(curvature[i]) >= CURVATURE_THRESHOLD for i in range(n)]
    corner_ids = [-1] * n

    current_id = 0
    in_corner = False
    start = -1

    for i in range(n):
        if is_corner[i] and not in_corner:
            in_corner = True
            start = i
        elif not is_corner[i] and in_corner:
            in_corner = False
            length = i - start
            if length >= MIN_CORNER_POINTS:
                for j in range(start, i):
                    corner_ids[j] = current_id
                current_id += 1
            else:
                # Too short, mark as straight
                for j in range(start, i):
                    is_corner[j] = False

    # Handle wrap: if still in corner at end
    if in_corner:
        length = n - start
        if length >= MIN_CORNER_POINTS:
            for j in range(start, n):
                corner_ids[j] = current_id
            current_id += 1
        else:
            for j in range(start, n):
                is_corner[j] = False

    return corner_ids, is_corner, current_id


# ─── Step 5: Corner Phase ───────────────────────────────────────────────────

def detect_corner_phases(curvature, corner_ids, num_corners):
    """Assign entry/apex/exit phase to each corner point.

    Returns phases[i] = 'entry' | 'apex' | 'exit' | 'straight'.
    """
    n = len(curvature)
    phases = ['straight'] * n

    for cid in range(num_corners):
        # Collect indices for this corner
        indices = [i for i in range(n) if corner_ids[i] == cid]
        if not indices:
            continue

        # Find apex = index of max |curvature|
        apex_idx = max(indices, key=lambda i: abs(curvature[i]))

        for i in indices:
            if i < apex_idx:
                phases[i] = 'entry'
            elif i == apex_idx:
                phases[i] = 'apex'
            else:
                phases[i] = 'exit'

    return phases


# ─── Step 6: Target Speed ───────────────────────────────────────────────────

def compute_target_speed(curvature):
    """Compute max cornering speed from curvature using v = sqrt(mu*g/|k|)."""
    n = len(curvature)
    speeds = [0.0] * n
    for i in range(n):
        k = abs(curvature[i])
        if k > 1e-6:
            v = math.sqrt(MU * G / k)
            speeds[i] = min(v, MAX_SPEED_MS)
        else:
            speeds[i] = MAX_SPEED_MS
    return speeds


# ─── Step 7: Smooth + Backward Braking Pass ─────────────────────────────────

def smooth_and_brake_limit(speeds, arc_length):
    """Smooth target speeds, then apply backward braking constraint."""
    n = len(speeds)

    # Forward smooth
    speeds = smooth_values(speeds, window=SPEED_SMOOTH_WINDOW)

    # Backward pass: braking physics constraint
    # v[i] = min(v[i], sqrt(v[i+1]^2 + 2 * a_max * ds))
    for i in range(n - 2, -1, -1):
        i_next = (i + 1) % n
        ds = abs(arc_length[i_next] - arc_length[i])
        if ds < 0.001:
            ds = 1.0
        v_brake = math.sqrt(speeds[i_next] ** 2 + 2 * A_MAX_BRAKE * ds)
        speeds[i] = min(speeds[i], v_brake)

    return speeds


# ─── Step 8: Validation ─────────────────────────────────────────────────────

def validate(curvature, speeds, corner_ids, num_corners, phases):
    """Print validation metrics."""
    n = len(curvature)

    # Curvature spikes
    max_k = max(abs(k) for k in curvature)
    spikes = sum(1 for k in curvature if abs(k) > 0.05)

    # Speed sanity
    min_speed = min(speeds)
    max_speed = max(speeds)
    nan_count = sum(1 for v in speeds if math.isnan(v) or v < 0)

    # Corner stats
    corner_points = sum(1 for cid in corner_ids if cid >= 0)
    straight_points = n - corner_points
    apexes = sum(1 for p in phases if p == 'apex')

    print(f"  Curvature: max |k| = {max_k:.5f}, spikes > 0.05: {spikes}")
    print(f"  Speed: min = {min_speed:.1f} m/s ({min_speed * 3.6:.0f} km/h), "
          f"max = {max_speed:.1f} m/s ({max_speed * 3.6:.0f} km/h)")
    print(f"  Invalid speeds (NaN/negative): {nan_count}")
    print(f"  Corners: {num_corners} detected, {apexes} apexes")
    print(f"  Points: {corner_points} corner ({corner_points/n*100:.1f}%), "
          f"{straight_points} straight ({straight_points/n*100:.1f}%)")

    if spikes > 0:
        print(f"  WARNING: {spikes} curvature spikes > 0.05")
    if nan_count > 0:
        print(f"  WARNING: {nan_count} invalid speed values")
    if num_corners < 3:
        print(f"  WARNING: Only {num_corners} corners detected — threshold may be too high")
    if num_corners > 40:
        print(f"  WARNING: {num_corners} corners detected — may be over-segmented")


# ─── Step 9: Output ─────────────────────────────────────────────────────────

def write_output(output_path, track_id, us, vs, arc_length, heading,
                 curvature, corner_ids, phases, speeds):
    """Write track intelligence JSON."""
    n = len(us)
    intelligence = {
        "track_id": track_id,
        "num_points": n,
        "total_arc_length_m": round(arc_length[-1], 1),
        "parameters": {
            "mu": MU,
            "g": G,
            "max_speed_ms": MAX_SPEED_MS,
            "curvature_threshold": CURVATURE_THRESHOLD,
            "a_max_brake": A_MAX_BRAKE,
        },
        "points": [
            {
                "s": round(arc_length[i], 2),
                "u": round(us[i], 3),
                "v": round(vs[i], 3),
                "heading": round(heading[i], 5),
                "curvature": round(curvature[i], 6),
                "corner_id": corner_ids[i],
                "corner_phase": phases[i],
                "target_speed": round(speeds[i], 2),
            }
            for i in range(n)
        ]
    }

    with open(output_path, 'w') as f:
        json.dump(intelligence, f, indent=2)


# ─── Main ───────────────────────────────────────────────────────────────────

def main():
    output_path = None
    map_path = None

    args = sys.argv[1:]
    i = 0
    while i < len(args):
        if args[i] == '-o' and i + 1 < len(args):
            output_path = args[i + 1]
            i += 2
        elif args[i].startswith('-'):
            print(f"Unknown option: {args[i]}")
            sys.exit(1)
        else:
            map_path = args[i]
            i += 1

    if not map_path:
        print("F1 2025 Track Intelligence Builder")
        print("=" * 40)
        print()
        print("Usage: python3 track_intelligence.py <track_map.json> [-o output.json]")
        print()
        print("Computes per-point curvature, corner detection, and target speed")
        print("from an existing spline-based track map.")
        print()
        print("Examples:")
        print('  python3 track_intelligence.py "Track Map Builds/track_0_true_map.json"')
        print('  python3 track_intelligence.py map.json -o melbourne_intel.json')
        sys.exit(1)

    print("F1 2025 Track Intelligence Builder")
    print("=" * 40)

    # Load track map
    print(f"\nLoading track map: {map_path}")
    with open(map_path) as f:
        data = json.load(f)

    points = data['points']
    us = [p['u'] for p in points]
    vs = [p['v'] for p in points]
    track_id = data.get('track_id')
    n = len(us)
    print(f"  Points: {n}")
    print(f"  Track ID: {track_id}")

    # Step 1: Arc length
    print("\nStep 1: Computing arc length...")
    arc_length = compute_arc_length(us, vs)
    print(f"  Total arc length: {arc_length[-1]:.1f}m")

    # Step 2: Heading
    print("Step 2: Computing heading...")
    heading = compute_heading(us, vs)

    # Step 3: Curvature
    print("Step 3: Computing curvature...")
    curvature = compute_curvature(heading, arc_length)
    print(f"  Smoothing curvature (window={CURVATURE_SMOOTH_WINDOW})...")
    curvature = smooth_values(curvature, window=CURVATURE_SMOOTH_WINDOW)
    # Clamp curvature spikes to realistic maximum
    clamped = sum(1 for k in curvature if abs(k) > CURVATURE_MAX)
    curvature = [max(-CURVATURE_MAX, min(CURVATURE_MAX, k)) for k in curvature]
    if clamped > 0:
        print(f"  Clamped {clamped} curvature spikes to ±{CURVATURE_MAX}")

    # Step 4: Corner detection
    print("Step 4: Detecting corners...")
    corner_ids, is_corner, num_corners = detect_corners(curvature)
    print(f"  {num_corners} corners detected (threshold={CURVATURE_THRESHOLD})")

    # Step 5: Corner phases
    print("Step 5: Assigning corner phases...")
    phases = detect_corner_phases(curvature, corner_ids, num_corners)

    # Step 6: Target speed
    print("Step 6: Computing target speed (mu={}, g={})...".format(MU, G))
    speeds = compute_target_speed(curvature)

    # Step 7: Smooth + braking constraint
    print("Step 7: Smoothing speed + backward braking pass...")
    speeds = smooth_and_brake_limit(speeds, arc_length)

    # Step 8: Validation
    print("\nValidation:")
    validate(curvature, speeds, corner_ids, num_corners, phases)

    # Step 9: Output
    MAP_OUTPUT_DIR = "Track Map Builds"
    os.makedirs(MAP_OUTPUT_DIR, exist_ok=True)
    if output_path is None:
        track_name = f"track_{track_id}" if track_id is not None else "track_unknown"
        output_path = os.path.join(MAP_OUTPUT_DIR, f"{track_name}_intelligence.json")

    write_output(output_path, track_id, us, vs, arc_length, heading,
                 curvature, corner_ids, phases, speeds)

    print(f"\nTrack intelligence written to {output_path}")
    print(f"  Points: {n}")
    print(f"  Corners: {num_corners}")
    print(f"  Speed range: {min(speeds)*3.6:.0f} - {max(speeds)*3.6:.0f} km/h")


if __name__ == '__main__':
    main()
