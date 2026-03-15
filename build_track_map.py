#!/usr/bin/env python3
"""
F1 2025 Track Map Builder

Reads recorded telemetry JSONL and generates a 2D track map.
Maps lap distance (meters) to 2D coordinates: C(s) -> (u, v)

Usage:
    python3 build_track_map.py <telemetry.jsonl> [output.json]
"""

import json
import sys
import math


# ─── Phase 1: Load Samples ───────────────────────────────────────────────────

def load_samples(jsonl_path):
    """Read JSONL file and extract per-frame telemetry for track mapping."""
    samples = []
    track_length = None
    track_id = None

    with open(jsonl_path) as f:
        for line in f:
            if not line.startswith('{'):
                continue
            try:
                data = json.loads(line.strip())
            except json.JSONDecodeError:
                continue

            meta = data.get('meta', {})
            player = data.get('player', {})
            world_pos = player.get('world_pos_m')
            if world_pos is None:
                continue

            # Skip frames with zero position (before first motion packet)
            x, y, z = world_pos.get('x', 0), world_pos.get('y', 0), world_pos.get('z', 0)
            if x == 0 and y == 0 and z == 0:
                continue

            tl = meta.get('track_length')
            if tl and tl > 0:
                track_length = tl
            if meta.get('track_id') is not None:
                track_id = meta.get('track_id')

            samples.append({
                'lap': player.get('lapNumber', 0),
                'dist': player.get('lapDistance', 0.0),
                'x': x,
                'y': y,
                'z': z,
            })

    return samples, track_length, track_id


# ─── Phase 2: Detect Map Plane ───────────────────────────────────────────────

def detect_plane(samples):
    """Identify vertical axis (smallest variance) and return (u_key, v_key, height_key)."""
    axes = ['x', 'y', 'z']
    variances = {}
    for axis in axes:
        vals = [s[axis] for s in samples]
        mean = sum(vals) / len(vals)
        variances[axis] = sum((v - mean) ** 2 for v in vals) / len(vals)

    height_axis = min(variances, key=variances.get)
    remaining = [a for a in axes if a != height_axis]
    return remaining[0], remaining[1], height_axis


# ─── Phase 3: Segment Into Laps ──────────────────────────────────────────────

def segment_laps(samples, track_length):
    """Group samples by lap number, discard partial laps."""
    laps = {}
    for s in samples:
        lap_num = s['lap']
        laps.setdefault(lap_num, []).append(s)

    complete_laps = []
    for lap_num in sorted(laps.keys()):
        lap_samples = laps[lap_num]
        if len(lap_samples) < 100:
            continue

        # Check distance coverage
        dists = [s['dist'] for s in lap_samples]
        # Filter out negative distances (near start/finish wrap)
        positive_dists = [d for d in dists if d >= 0]
        if not positive_dists:
            continue

        coverage = max(positive_dists) - min(positive_dists)
        if coverage < track_length * 0.8:
            continue

        # Filter to positive distances only and sort
        filtered = [s for s in lap_samples if s['dist'] >= 0]
        filtered.sort(key=lambda s: s['dist'])
        complete_laps.append(filtered)

    return complete_laps


# ─── Phase 4: Resample by Distance ───────────────────────────────────────────

def resample_lap(lap_samples, u_key, v_key, track_length):
    """Resample a single lap to 1m spacing via linear interpolation."""
    dists = [s['dist'] for s in lap_samples]
    us = [s[u_key] for s in lap_samples]
    vs = [s[v_key] for s in lap_samples]

    n_points = int(track_length)
    resampled_u = []
    resampled_v = []
    j = 0

    for target in range(n_points):
        target_f = float(target)

        # Advance j to bracket target
        while j < len(dists) - 1 and dists[j + 1] < target_f:
            j += 1

        if j >= len(dists) - 1:
            resampled_u.append(us[-1])
            resampled_v.append(vs[-1])
            continue

        d0, d1 = dists[j], dists[j + 1]
        if abs(d1 - d0) < 0.001:
            t = 0.0
        else:
            t = (target_f - d0) / (d1 - d0)
            t = max(0.0, min(1.0, t))

        resampled_u.append(us[j] + t * (us[j + 1] - us[j]))
        resampled_v.append(vs[j] + t * (vs[j + 1] - vs[j]))

    return resampled_u, resampled_v


# ─── Phase 5: Average Multiple Laps ──────────────────────────────────────────

def average_laps(resampled_laps):
    """Average (u, v) across multiple laps at each distance point."""
    n_laps = len(resampled_laps)
    n_points = len(resampled_laps[0][0])

    avg_u = [0.0] * n_points
    avg_v = [0.0] * n_points

    for u_arr, v_arr in resampled_laps:
        for i in range(n_points):
            avg_u[i] += u_arr[i]
            avg_v[i] += v_arr[i]

    avg_u = [u / n_laps for u in avg_u]
    avg_v = [v / n_laps for v in avg_v]
    return avg_u, avg_v


# ─── Phase 6: Close the Loop ─────────────────────────────────────────────────

def close_loop(avg_u, avg_v, blend_meters=20):
    """Blend start and end to ensure a closed loop."""
    n = len(avg_u)
    if n < blend_meters * 2:
        return avg_u, avg_v

    # Compute midpoint between start and end
    mid_u = (avg_u[0] + avg_u[-1]) / 2.0
    mid_v = (avg_v[0] + avg_v[-1]) / 2.0

    for i in range(blend_meters):
        t = i / blend_meters  # 0 at edge, approaches 1

        # Blend start region toward midpoint
        avg_u[i] = avg_u[i] * t + mid_u * (1 - t)
        avg_v[i] = avg_v[i] * t + mid_v * (1 - t)

        # Blend end region toward midpoint
        j = n - 1 - i
        avg_u[j] = avg_u[j] * t + mid_u * (1 - t)
        avg_v[j] = avg_v[j] * t + mid_v * (1 - t)

    return avg_u, avg_v


# ─── Validation ──────────────────────────────────────────────────────────────

def validate(resampled_laps, avg_u, avg_v):
    """Print validation metrics."""
    # 1. Wrap-point discontinuity
    gap_u = avg_u[0] - avg_u[-1]
    gap_v = avg_v[0] - avg_v[-1]
    gap = math.sqrt(gap_u ** 2 + gap_v ** 2)
    print(f"  Wrap-point gap: {gap:.3f}m")

    # 2. Mean lateral variance across laps
    if len(resampled_laps) > 1:
        n_points = len(avg_u)
        total_var = 0.0
        for i in range(n_points):
            vals_u = [lap[0][i] for lap in resampled_laps]
            vals_v = [lap[1][i] for lap in resampled_laps]
            mean_u = sum(vals_u) / len(vals_u)
            mean_v = sum(vals_v) / len(vals_v)
            var = sum((u - mean_u) ** 2 + (v - mean_v) ** 2
                      for u, v in zip(vals_u, vals_v)) / len(vals_u)
            total_var += var
        mean_var = total_var / n_points
        print(f"  Mean lateral variance: {mean_var:.4f}m² (std: {math.sqrt(mean_var):.3f}m)")
    else:
        print("  Mean lateral variance: N/A (single lap)")


# ─── Output ──────────────────────────────────────────────────────────────────

def write_track_map(output_path, track_id, track_length, u_key, v_key, avg_u, avg_v):
    """Write track map JSON file."""
    track_map = {
        "track_id": track_id,
        "track_length_m": track_length,
        "coordinate_axes": {"u": u_key, "v": v_key},
        "spacing_m": 1,
        "num_points": len(avg_u),
        "points": [
            {"s": i, "u": round(avg_u[i], 3), "v": round(avg_v[i], 3)}
            for i in range(len(avg_u))
        ]
    }

    with open(output_path, 'w') as f:
        json.dump(track_map, f, indent=2)


# ─── Main ────────────────────────────────────────────────────────────────────

def main():
    if len(sys.argv) < 2:
        print("Usage: python3 build_track_map.py <telemetry.jsonl> [output.json]")
        print()
        print("Build a 2D track map from recorded F1 2025 telemetry data.")
        print("Record telemetry first using: ./record.sh")
        sys.exit(1)

    jsonl_path = sys.argv[1]
    output_path = sys.argv[2] if len(sys.argv) > 2 else None

    print("F1 2025 Track Map Builder")
    print("=" * 40)

    # Phase 1: Load samples
    print(f"\nLoading telemetry from {jsonl_path}...")
    samples, track_length, track_id = load_samples(jsonl_path)

    if not samples:
        print("ERROR: No valid samples found.")
        print("  Ensure the recording contains player.world_pos_m data.")
        print("  You may need to re-record with the latest telemetry system.")
        sys.exit(1)

    if track_length is None:
        print("ERROR: No track_length found in meta data.")
        print("  Ensure the recording contains meta.track_length.")
        sys.exit(1)

    print(f"  Samples: {len(samples)}")
    print(f"  Track ID: {track_id}")
    print(f"  Track length: {track_length}m")

    # Phase 2: Detect map plane
    u_key, v_key, h_key = detect_plane(samples)
    print(f"\nMap plane: ({u_key}, {v_key}), height axis: {h_key}")

    # Phase 3: Segment into complete laps
    laps = segment_laps(samples, track_length)
    print(f"Complete laps found: {len(laps)}")

    if len(laps) < 1:
        print("ERROR: No complete laps found.")
        print("  Need at least 1 full lap (>80% track coverage).")
        print("  Try recording more laps or driving cleaner lines.")
        sys.exit(1)

    for i, lap in enumerate(laps):
        dists = [s['dist'] for s in lap]
        print(f"  Lap {i + 1}: {len(lap)} samples, "
              f"dist {min(dists):.0f}-{max(dists):.0f}m")

    # Phase 4: Resample each lap to 1m spacing
    print(f"\nResampling {len(laps)} lap(s) to 1m spacing...")
    resampled = []
    for lap in laps:
        r = resample_lap(lap, u_key, v_key, track_length)
        resampled.append(r)

    # Phase 5: Average across laps
    print("Averaging across laps...")
    avg_u, avg_v = average_laps(resampled)

    # Phase 6: Close the loop
    print("Closing loop...")
    avg_u, avg_v = close_loop(avg_u, avg_v)

    # Validation
    print("\nValidation:")
    validate(resampled, avg_u, avg_v)

    # Output
    if output_path is None:
        track_name = f"track_{track_id}" if track_id is not None else "track_unknown"
        output_path = f"{track_name}_map.json"

    write_track_map(output_path, track_id, track_length, u_key, v_key, avg_u, avg_v)

    print(f"\nTrack map written to {output_path}")
    print(f"  Points: {len(avg_u)}")
    print(f"  Spacing: 1m")
    print(f"  Format: C(s) -> (u={u_key}, v={v_key})")


if __name__ == '__main__':
    main()
