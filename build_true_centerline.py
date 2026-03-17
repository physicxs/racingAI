#!/usr/bin/env python3
"""
F1 2025 True Track Centerline Builder

Computes a true geometric centerline from track edges by analyzing
multiple laps with varied lateral positions. Unlike the basic track map
builder (which uses the driven path as centerline), this produces an
unbiased centerline at the midpoint between left/right track edges.

Workflow:
    1. Record 3-5 laps with varied lines (left, right, normal)
    2. Run this script on the recording(s)
    3. Use the output map with track_map_live.py

Usage:
    python3 build_true_centerline.py <file1.jsonl> [file2.jsonl ...] [-o output.json]
"""

import json
import sys
import math


# ─── Phase 1: Load Samples ──────────────────────────────────────────────────

def load_all_samples(jsonl_paths):
    """Load telemetry samples from one or more JSONL files."""
    all_samples = []
    track_length = None
    track_id = None

    for path in jsonl_paths:
        file_samples = 0
        with open(path) as f:
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

                x = world_pos.get('x', 0)
                y = world_pos.get('y', 0)
                z = world_pos.get('z', 0)
                if x == 0 and y == 0 and z == 0:
                    continue

                tl = meta.get('track_length')
                if tl and tl > 0:
                    track_length = tl
                if meta.get('track_id') is not None:
                    track_id = meta.get('track_id')

                all_samples.append({
                    'lap': player.get('lapNumber', 0),
                    'dist': player.get('lapDistance', 0.0),
                    'x': x, 'y': y, 'z': z,
                    'source': path,
                })
                file_samples += 1
        print(f"  {path}: {file_samples} samples")

    return all_samples, track_length, track_id


# ─── Phase 2: Detect Map Plane ──────────────────────────────────────────────

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


# ─── Phase 3: Build Reference Path ──────────────────────────────────────────

def segment_complete_laps(samples, track_length):
    """Group samples by (source, lap), keep laps with >80% coverage."""
    laps = {}
    for s in samples:
        key = (s.get('source', ''), s['lap'])
        laps.setdefault(key, []).append(s)

    complete = []
    for key in sorted(laps.keys()):
        lap_samples = laps[key]
        if len(lap_samples) < 100:
            continue
        positive = [s for s in lap_samples if s['dist'] >= 0]
        if not positive:
            continue
        dists = [s['dist'] for s in positive]
        if max(dists) - min(dists) < track_length * 0.8:
            continue
        positive.sort(key=lambda s: s['dist'])
        complete.append(positive)

    return complete


def resample_lap(lap_samples, u_key, v_key, n_points):
    """Resample a single lap to 1m spacing via linear interpolation."""
    dists = [s['dist'] for s in lap_samples]
    us = [s[u_key] for s in lap_samples]
    vs = [s[v_key] for s in lap_samples]

    r_u = []
    r_v = []
    j = 0

    for target in range(n_points):
        target_f = float(target)
        while j < len(dists) - 1 and dists[j + 1] < target_f:
            j += 1
        if j >= len(dists) - 1:
            r_u.append(us[-1])
            r_v.append(vs[-1])
            continue
        d0, d1 = dists[j], dists[j + 1]
        if abs(d1 - d0) < 0.001:
            t = 0.0
        else:
            t = max(0.0, min(1.0, (target_f - d0) / (d1 - d0)))
        r_u.append(us[j] + t * (us[j + 1] - us[j]))
        r_v.append(vs[j] + t * (vs[j + 1] - vs[j]))

    return r_u, r_v


def build_reference_path(laps, u_key, v_key, track_length):
    """Build a rough reference path by averaging all complete laps."""
    n_points = int(track_length)

    resampled = []
    for lap in laps:
        r_u, r_v = resample_lap(lap, u_key, v_key, n_points)
        resampled.append((r_u, r_v))

    # Average across laps
    avg_u = [0.0] * n_points
    avg_v = [0.0] * n_points
    n = len(resampled)
    for r_u, r_v in resampled:
        for i in range(n_points):
            avg_u[i] += r_u[i]
            avg_v[i] += r_v[i]
    avg_u = [u / n for u in avg_u]
    avg_v = [v / n for v in avg_v]

    return avg_u, avg_v


def compute_normals(ref_u, ref_v):
    """Compute perpendicular normal vectors at each reference path point."""
    n = len(ref_u)
    normals_u = [0.0] * n
    normals_v = [0.0] * n

    for i in range(n):
        i_next = (i + 1) % n
        du = ref_u[i_next] - ref_u[i]
        dv = ref_v[i_next] - ref_v[i]
        length = math.sqrt(du * du + dv * dv)
        if length < 1e-9:
            if i > 0:
                normals_u[i] = normals_u[i - 1]
                normals_v[i] = normals_v[i - 1]
            continue
        fu = du / length
        fv = dv / length
        # Right perpendicular: cross(forward, up) projected to 2D
        normals_u[i] = -fv
        normals_v[i] = fu

    return normals_u, normals_v


# ─── Phase 4: Compute Lateral Offsets ────────────────────────────────────────

def compute_lateral_offsets(samples, ref_u, ref_v, normals_u, normals_v,
                            u_key, v_key, track_length):
    """Project every sample onto the reference path, compute lateral offset.

    Returns a dict: bin_index -> list of lateral offsets.
    """
    n = len(ref_u)
    search_radius = 50
    offsets_by_bin = {i: [] for i in range(n)}

    for s in samples:
        car_u = s[u_key]
        car_v = s[v_key]
        dist = s['dist']
        if dist < 0:
            continue

        center_idx = int(dist % track_length)
        if center_idx >= n:
            center_idx = n - 1

        best_dist_sq = float('inf')
        best_seg_idx = center_idx
        best_proj_u = ref_u[center_idx]
        best_proj_v = ref_v[center_idx]

        for offset in range(-search_radius, search_radius + 1):
            i = (center_idx + offset) % n
            i_next = (i + 1) % n

            seg_u = ref_u[i_next] - ref_u[i]
            seg_v = ref_v[i_next] - ref_v[i]
            seg_len_sq = seg_u * seg_u + seg_v * seg_v
            if seg_len_sq < 1e-12:
                continue

            wu = car_u - ref_u[i]
            wv = car_v - ref_v[i]
            t = (wu * seg_u + wv * seg_v) / seg_len_sq
            t = max(0.0, min(1.0, t))

            proj_u = ref_u[i] + seg_u * t
            proj_v = ref_v[i] + seg_v * t
            du = car_u - proj_u
            dv = car_v - proj_v
            d_sq = du * du + dv * dv

            if d_sq < best_dist_sq:
                best_dist_sq = d_sq
                best_seg_idx = i
                best_proj_u = proj_u
                best_proj_v = proj_v

        # Compute lateral offset using local right vector
        nu = normals_u[best_seg_idx]
        nv = normals_v[best_seg_idx]
        du = car_u - best_proj_u
        dv = car_v - best_proj_v
        lateral = du * nu + dv * nv

        offsets_by_bin[best_seg_idx].append(lateral)

    return offsets_by_bin


# ─── Phase 5: Edge Detection ────────────────────────────────────────────────

def percentile(sorted_values, p):
    """Compute p-th percentile from sorted values (0-100)."""
    if not sorted_values:
        return 0.0
    k = (len(sorted_values) - 1) * p / 100.0
    f = int(k)
    c = f + 1
    if c >= len(sorted_values):
        return sorted_values[-1]
    return sorted_values[f] + (k - f) * (sorted_values[c] - sorted_values[f])


DEFAULT_HALF_WIDTH = 7.0  # fallback for bins with too few samples


def detect_edges(offsets_by_bin, n_bins):
    """Compute left/right edges per bin using robust percentiles.

    Returns (left_edges, right_edges) arrays.
    """
    left_edges = [0.0] * n_bins
    right_edges = [0.0] * n_bins
    good_bins = 0

    for i in range(n_bins):
        vals = sorted(offsets_by_bin.get(i, []))
        if len(vals) < 5:
            # Not enough data, use default
            left_edges[i] = -DEFAULT_HALF_WIDTH
            right_edges[i] = DEFAULT_HALF_WIDTH
            continue

        left_edges[i] = percentile(vals, 5)
        right_edges[i] = percentile(vals, 95)
        good_bins += 1

        # Sanity: ensure edges are separated
        if right_edges[i] - left_edges[i] < 4.0:
            # Track must be at least 4m wide
            mid = (left_edges[i] + right_edges[i]) / 2.0
            left_edges[i] = mid - DEFAULT_HALF_WIDTH
            right_edges[i] = mid + DEFAULT_HALF_WIDTH

    print(f"  Bins with enough data: {good_bins}/{n_bins}")
    return left_edges, right_edges


# ─── Phase 6: Compute True Centerline ───────────────────────────────────────

def compute_true_centerline(ref_u, ref_v, normals_u, normals_v,
                             left_edges, right_edges):
    """Compute true centerline as midpoint between edges.

    Returns (center_u, center_v, half_widths).
    """
    n = len(ref_u)
    center_u = [0.0] * n
    center_v = [0.0] * n
    half_widths = [0.0] * n

    for i in range(n):
        center_offset = (left_edges[i] + right_edges[i]) / 2.0
        half_widths[i] = (right_edges[i] - left_edges[i]) / 2.0

        # Shift reference point by center_offset along normal
        center_u[i] = ref_u[i] + normals_u[i] * center_offset
        center_v[i] = ref_v[i] + normals_v[i] * center_offset

    return center_u, center_v, half_widths


# ─── Phase 7: Smoothing ─────────────────────────────────────────────────────

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


def close_loop(center_u, center_v, blend_meters=20):
    """Blend start/end to ensure a closed loop."""
    n = len(center_u)
    if n < blend_meters * 2:
        return center_u, center_v

    mid_u = (center_u[0] + center_u[-1]) / 2.0
    mid_v = (center_v[0] + center_v[-1]) / 2.0

    for i in range(blend_meters):
        t = i / blend_meters
        center_u[i] = center_u[i] * t + mid_u * (1 - t)
        center_v[i] = center_v[i] * t + mid_v * (1 - t)
        j = n - 1 - i
        center_u[j] = center_u[j] * t + mid_u * (1 - t)
        center_v[j] = center_v[j] * t + mid_v * (1 - t)

    return center_u, center_v


# ─── Phase 8: Output ────────────────────────────────────────────────────────

def write_track_map(output_path, track_id, track_length, u_key, v_key,
                    center_u, center_v, half_widths):
    """Write track map JSON with per-point half_width."""
    track_map = {
        "track_id": track_id,
        "track_length_m": track_length,
        "coordinate_axes": {"u": u_key, "v": v_key},
        "spacing_m": 1,
        "num_points": len(center_u),
        "true_centerline": True,
        "points": [
            {
                "s": i,
                "u": round(center_u[i], 3),
                "v": round(center_v[i], 3),
                "half_width": round(half_widths[i], 2),
            }
            for i in range(len(center_u))
        ]
    }

    with open(output_path, 'w') as f:
        json.dump(track_map, f, indent=2)


# ─── Validation ─────────────────────────────────────────────────────────────

def validate(center_u, center_v, half_widths, ref_u, ref_v):
    """Print validation metrics."""
    n = len(center_u)

    # Wrap gap
    gap_u = center_u[0] - center_u[-1]
    gap_v = center_v[0] - center_v[-1]
    gap = math.sqrt(gap_u ** 2 + gap_v ** 2)
    print(f"  Wrap-point gap: {gap:.3f}m")

    # Centerline shift from reference
    shifts = []
    for i in range(n):
        du = center_u[i] - ref_u[i]
        dv = center_v[i] - ref_v[i]
        shifts.append(math.sqrt(du * du + dv * dv))
    avg_shift = sum(shifts) / len(shifts)
    max_shift = max(shifts)
    print(f"  Avg centerline shift from racing line: {avg_shift:.2f}m")
    print(f"  Max centerline shift from racing line: {max_shift:.2f}m")

    # Width statistics
    avg_width = sum(half_widths) / len(half_widths) * 2
    min_width = min(half_widths) * 2
    max_width = max(half_widths) * 2
    print(f"  Track width: avg={avg_width:.1f}m, min={min_width:.1f}m, max={max_width:.1f}m")


# ─── Main ───────────────────────────────────────────────────────────────────

def main():
    # Parse args
    output_path = None
    jsonl_paths = []

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
            jsonl_paths.append(args[i])
            i += 1

    if not jsonl_paths:
        print("F1 2025 True Track Centerline Builder")
        print("=" * 45)
        print()
        print("Usage: python3 build_true_centerline.py <file1.jsonl> [file2.jsonl ...] [-o output.json]")
        print()
        print("Computes a true geometric centerline from track edges.")
        print("For best results, record 3-5 laps with varied lateral positions:")
        print("  - Some laps staying left")
        print("  - Some laps staying right")
        print("  - Some laps on the normal racing line")
        print()
        print("Examples:")
        print("  python3 build_true_centerline.py race1.jsonl")
        print("  python3 build_true_centerline.py left.jsonl right.jsonl normal.jsonl")
        print("  python3 build_true_centerline.py race.jsonl -o monaco_true_map.json")
        sys.exit(1)

    print("F1 2025 True Track Centerline Builder")
    print("=" * 45)

    # Phase 1: Load
    print(f"\nLoading telemetry from {len(jsonl_paths)} file(s)...")
    samples, track_length, track_id = load_all_samples(jsonl_paths)

    if not samples:
        print("ERROR: No valid samples found.")
        sys.exit(1)
    if track_length is None:
        print("ERROR: No track_length found in meta data.")
        sys.exit(1)

    print(f"\n  Total samples: {len(samples)}")
    print(f"  Track ID: {track_id}")
    print(f"  Track length: {track_length}m")

    # Phase 2: Detect plane
    u_key, v_key, h_key = detect_plane(samples)
    print(f"\nMap plane: ({u_key}, {v_key}), height axis: {h_key}")

    # Phase 3: Segment into complete laps
    laps = segment_complete_laps(samples, track_length)
    print(f"Complete laps found: {len(laps)}")

    if len(laps) < 1:
        print("ERROR: No complete laps found (need >80% track coverage).")
        sys.exit(1)

    if len(laps) < 3:
        print("WARNING: Only {} lap(s) found. For accurate edge detection,".format(len(laps)))
        print("         record 3-5 laps with varied lateral positions.")

    for i, lap in enumerate(laps):
        dists = [s['dist'] for s in lap]
        print(f"  Lap {i + 1}: {len(lap)} samples, dist {min(dists):.0f}-{max(dists):.0f}m")

    # Phase 3b: Build reference path (rough centerline)
    print(f"\nBuilding reference path from {len(laps)} lap(s)...")
    ref_u, ref_v = build_reference_path(laps, u_key, v_key, track_length)
    normals_u, normals_v = compute_normals(ref_u, ref_v)

    n_points = len(ref_u)
    print(f"  Reference path: {n_points} points at 1m spacing")

    # Phase 4: Compute lateral offsets for ALL samples
    print("\nComputing lateral offsets for all samples...")
    offsets_by_bin = compute_lateral_offsets(
        samples, ref_u, ref_v, normals_u, normals_v, u_key, v_key, track_length)

    total_offsets = sum(len(v) for v in offsets_by_bin.values())
    print(f"  Total offset measurements: {total_offsets}")

    # Phase 5: Edge detection (percentile-based)
    print("\nDetecting track edges (5th/95th percentile)...")
    left_edges, right_edges = detect_edges(offsets_by_bin, n_points)

    # Phase 6: True centerline
    print("\nComputing true centerline...")
    center_u, center_v, half_widths = compute_true_centerline(
        ref_u, ref_v, normals_u, normals_v, left_edges, right_edges)

    # Phase 7: Smooth
    print("Smoothing centerline and width (window=10)...")
    center_u = smooth_values(center_u, window=10)
    center_v = smooth_values(center_v, window=10)
    half_widths = smooth_values(half_widths, window=10)

    # Close the loop
    center_u, center_v = close_loop(center_u, center_v)

    # Validation
    print("\nValidation:")
    validate(center_u, center_v, half_widths, ref_u, ref_v)

    # Output
    if output_path is None:
        track_name = f"track_{track_id}" if track_id is not None else "track_unknown"
        output_path = f"{track_name}_true_map.json"

    write_track_map(output_path, track_id, track_length, u_key, v_key,
                    center_u, center_v, half_widths)

    print(f"\nTrue centerline map written to {output_path}")
    print(f"  Points: {n_points}")
    print(f"  Format: C(s) -> (u={u_key}, v={v_key}, half_width)")
    print(f"\nUse with: ./track_map_gui.sh {output_path}")


if __name__ == '__main__':
    main()
