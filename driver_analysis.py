#!/usr/bin/env python3
"""
F1 2025 Player vs Track Analysis

Evaluates driver performance against the track intelligence model.
Computes per-corner scores based on entry/apex/exit quality.

Usage:
    python3 driver_analysis.py <intelligence.json> <telemetry.jsonl> [-o output.json]
"""

import json
import sys
import os
import math
from collections import defaultdict


# ─── Tunable Parameters ─────────────────────────────────────────────────────

SPEED_DELTA_THRESHOLD = 5.0   # m/s — threshold for braking errors
APEX_LATERAL_THRESHOLD = 2.0  # meters — missed apex threshold
EXIT_THROTTLE_THRESHOLD = 0.8 # throttle below this = poor exit

PENALTY_EARLY_BRAKE = 10
PENALTY_LATE_BRAKE = 15
PENALTY_MISSED_APEX = 20
PENALTY_POOR_EXIT = 25

SEARCH_WINDOW = 100  # points to search around estimated index


# ─── Step 1: Map Car Position to Track ───────────────────────────────────────

def build_track_index(intel_points):
    """Precompute arrays for fast nearest-point lookup."""
    us = [p['u'] for p in intel_points]
    vs = [p['v'] for p in intel_points]
    return us, vs


def find_nearest_track_index(car_u, car_v, us, vs, hint_idx, n):
    """Find nearest track point using segment-based projection.

    Searches a window around hint_idx for efficiency.
    """
    best_dist = float('inf')
    best_idx = hint_idx

    start = hint_idx - SEARCH_WINDOW
    end = hint_idx + SEARCH_WINDOW

    for i in range(start, end):
        idx = i % n
        du = car_u - us[idx]
        dv = car_v - vs[idx]
        dist_sq = du * du + dv * dv
        if dist_sq < best_dist:
            best_dist = dist_sq
            best_idx = idx

    return best_idx


def map_lap_distance_to_index(lap_distance, intel_points, total_arc):
    """Estimate track index from lapDistance for search hint."""
    if total_arc <= 0:
        return 0
    n = len(intel_points)
    # lapDistance wraps at track_length, arc_length is similar
    frac = (lap_distance % total_arc) / total_arc
    return int(frac * n) % n


# ─── Step 2: Per-Frame Features ──────────────────────────────────────────────

def compute_lateral_offset(car_u, car_v, track_u, track_v, heading):
    """Compute signed lateral offset from centerline.

    Positive = right of centerline, negative = left.
    """
    dx = car_u - track_u
    dy = car_v - track_v
    return dx * (-math.sin(heading)) + dy * math.cos(heading)


# ─── Main Analysis ───────────────────────────────────────────────────────────

def analyze(intel_path, telemetry_path):
    """Run full driver analysis pipeline."""

    # Load track intelligence
    print(f"Loading track intelligence: {intel_path}")
    with open(intel_path) as f:
        intel = json.load(f)

    intel_points = intel['points']
    n = len(intel_points)
    total_arc = intel['total_arc_length_m']
    us, vs = build_track_index(intel_points)

    # Load coordinate axes from track map (for world→2D mapping)
    # Intelligence uses u/v which map to world x/z for this track
    # We read these from the track map if available, default to x/z
    u_axis = 'x'
    v_axis = 'z'

    print(f"  Points: {n}, Arc length: {total_arc:.0f}m")
    num_corners = max((p['corner_id'] for p in intel_points), default=-1) + 1
    print(f"  Corners: {num_corners}")

    # Load telemetry
    print(f"\nLoading telemetry: {telemetry_path}")
    frames = []
    with open(telemetry_path) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                frames.append(json.loads(line))
            except json.JSONDecodeError:
                continue

    print(f"  Frames: {len(frames)}")

    # Filter to valid frames with player data
    valid_frames = []
    for frame in frames:
        player = frame.get('player')
        if not player:
            continue
        world_pos = player.get('world_pos_m')
        if not world_pos:
            continue
        lap_dist = player.get('lapDistance', 0)
        if lap_dist < 0:
            continue  # pre-race positioning
        valid_frames.append(frame)

    print(f"  Valid frames (with position, lapDist >= 0): {len(valid_frames)}")
    if not valid_frames:
        print("ERROR: No valid frames found.")
        return None

    # Step 1: Map each frame to track position
    print("\nStep 1: Mapping frames to track...")
    raw_frame_data = []
    prev_idx = 0

    for frame in valid_frames:
        player = frame['player']
        world_pos = player['world_pos_m']

        car_u = world_pos[u_axis]
        car_v = world_pos[v_axis]

        lap_dist = player.get('lapDistance', 0)
        hint = map_lap_distance_to_index(lap_dist, intel_points, total_arc)

        idx = find_nearest_track_index(car_u, car_v, us, vs, hint, n)
        prev_idx = idx

        tp = intel_points[idx]

        lateral = compute_lateral_offset(car_u, car_v, tp['u'], tp['v'], tp['heading'])
        player_speed_ms = player['speed'] / 3.6

        raw_frame_data.append({
            'track_idx': idx,
            's': tp['s'],
            'corner_id': tp['corner_id'],
            'corner_phase': tp['corner_phase'],
            'lateral_offset': lateral,
            'player_speed_ms': player_speed_ms,
            'throttle': player.get('throttle', 0),
            'brake': player.get('brake', 0),
            'steering': abs(player.get('steering', 0)),
            'lap_number': player.get('lapNumber', 0),
            'session_time': frame.get('sessionTime', 0),
        })

    # Step 1b: Re-segment corner phases using telemetry signals
    print("Step 1b: Re-segmenting corner phases from driver inputs...")

    # Group frames by (corner_id, lap_number) to get individual passes
    corner_passes = defaultdict(list)
    for i, fd in enumerate(raw_frame_data):
        cid = fd['corner_id']
        if cid >= 0:
            corner_passes[(cid, fd['lap_number'])].append(i)

    BRAKE_THRESHOLD = 0.1
    THROTTLE_START = 0.2
    THROTTLE_STABLE = 0.8
    APEX_WINDOW_FRAMES = 15  # ~0.5s at 30Hz

    resegmented = 0
    for (cid, lap), indices in corner_passes.items():
        if len(indices) < 3:
            continue

        frames_slice = [raw_frame_data[i] for i in indices]
        speeds = [f['player_speed_ms'] for f in frames_slice]
        brakes = [f['brake'] for f in frames_slice]
        throttles = [f['throttle'] for f in frames_slice]
        steerings = [f['steering'] for f in frames_slice]

        nf = len(frames_slice)

        # --- Find entry start: first frame with brake > threshold ---
        entry_start = None
        for j in range(nf):
            if brakes[j] > BRAKE_THRESHOLD:
                entry_start = j
                break

        # --- Find apex: minimum speed point ---
        min_speed_idx = speeds.index(min(speeds))

        # --- Find entry end: min(speed local min, max steering) before apex ---
        # Entry ends at the earlier of: speed minimum or max steering
        entry_end = min_speed_idx  # default to speed minimum

        if entry_start is not None:
            # Look for max steering between entry_start and a bit past apex
            search_end = min(min_speed_idx + 5, nf)
            if entry_start < search_end:
                steer_region = steerings[entry_start:search_end]
                if steer_region:
                    max_steer_local = entry_start + steer_region.index(max(steer_region))
                    entry_end = min(entry_end, max_steer_local)

            # Entry end must be after entry start
            if entry_end <= entry_start:
                entry_end = min_speed_idx

        # --- Apex window: centered on min speed ---
        apex_start = max(0, min_speed_idx - APEX_WINDOW_FRAMES)
        apex_end = min(nf - 1, min_speed_idx + APEX_WINDOW_FRAMES)

        # Ensure apex doesn't overlap with entry
        if entry_start is not None:
            apex_start = max(apex_start, entry_end)

        # --- Find exit start: first frame after apex with throttle > 0.2 ---
        exit_start = None
        for j in range(apex_end, nf):
            if throttles[j] > THROTTLE_START:
                exit_start = j
                break

        # --- Find exit end: throttle stabilizes > 0.8, or corner ends ---
        exit_end = nf - 1
        if exit_start is not None:
            for j in range(exit_start, nf):
                if throttles[j] >= THROTTLE_STABLE:
                    exit_end = j
                    break

        # --- Assign phases ---
        for j, global_idx in enumerate(indices):
            if entry_start is not None and j >= entry_start and j < apex_start:
                raw_frame_data[global_idx]['corner_phase'] = 'entry'
            elif j >= apex_start and j <= apex_end:
                raw_frame_data[global_idx]['corner_phase'] = 'apex'
            elif exit_start is not None and j >= exit_start and j <= exit_end:
                raw_frame_data[global_idx]['corner_phase'] = 'exit'
            else:
                # Frames outside defined phases (pre-braking, post-exit)
                # Keep geometry phase as fallback
                pass
            resegmented += 1

    print(f"  Re-segmented {resegmented} frames across {len(corner_passes)} corner passes")

    # Step 1c: Build data-driven reference speeds
    print("Step 1c: Computing data-driven reference speeds...")
    corner_phase_speeds = defaultdict(lambda: defaultdict(list))
    for fd in raw_frame_data:
        cid = fd['corner_id']
        if cid >= 0:
            corner_phase_speeds[cid][fd['corner_phase']].append(fd['player_speed_ms'])

    REFERENCE_PERCENTILE = 75  # 75th pct — representative of good performance

    def percentile(values, pct):
        """Compute percentile from sorted values."""
        s = sorted(values)
        k = (len(s) - 1) * pct / 100.0
        f = int(k)
        c = f + 1 if f + 1 < len(s) else f
        d = k - f
        return s[f] + d * (s[c] - s[f])

    corner_targets = {}
    for cid in sorted(corner_phase_speeds.keys()):
        phases = corner_phase_speeds[cid]
        targets = {}
        for phase in ('entry', 'apex', 'exit'):
            speeds = phases.get(phase, [])
            if speeds:
                targets[f'{phase}_speed'] = round(percentile(speeds, REFERENCE_PERCENTILE), 2)
            else:
                targets[f'{phase}_speed'] = 0.0
        corner_targets[cid] = targets

    for cid, t in corner_targets.items():
        print(f"  Corner {cid}: entry={t['entry_speed']:.1f} apex={t['apex_speed']:.1f} exit={t['exit_speed']:.1f} m/s")

    # Step 2: Compute speed deltas against data-driven references
    print("Step 2: Computing features with data-driven targets...")
    frame_data = []
    for fd in raw_frame_data:
        cid = fd['corner_id']
        phase = fd['corner_phase']

        # Use data-driven reference if available, else fall back to 0 (no penalty)
        ref_speed = 0.0
        if cid >= 0 and cid in corner_targets:
            ref_speed = corner_targets[cid].get(f'{phase}_speed', 0.0)

        speed_delta = fd['player_speed_ms'] - ref_speed if ref_speed > 0 else 0.0

        frame_data.append({
            **fd,
            'speed_delta': speed_delta,
            'target_speed_ms': ref_speed,
        })

    # Validate mapping
    jumps = 0
    for i in range(1, len(frame_data)):
        diff = abs(frame_data[i]['track_idx'] - frame_data[i - 1]['track_idx'])
        if diff > n // 2:
            diff = n - diff  # wrap
        if diff > 50:
            jumps += 1
    print(f"  Large index jumps (>50): {jumps}")

    # Step 3: Group frames by corner
    print("\nStep 3: Grouping frames by corner...")
    corner_frames = defaultdict(list)
    for fd in frame_data:
        cid = fd['corner_id']
        if cid >= 0:
            corner_frames[cid].append(fd)

    print(f"  Corners with data: {len(corner_frames)}/{num_corners}")

    # Step 4: Detect errors, compute scores, aggregate
    print("Step 4: Computing corner scores...")
    corner_results = []

    for cid in sorted(corner_frames.keys()):
        cframes = corner_frames[cid]

        entry_frames = [f for f in cframes if f['corner_phase'] == 'entry']
        apex_frames = [f for f in cframes if f['corner_phase'] == 'apex']
        exit_frames = [f for f in cframes if f['corner_phase'] == 'exit']

        # --- Entry score: based on speed ratio at corner entry ---
        entry_score = 100
        if entry_frames:
            # Ratio of actual to target speed (1.0 = perfect)
            ratios = []
            for f in entry_frames:
                if f['target_speed_ms'] > 1:
                    ratios.append(f['player_speed_ms'] / f['target_speed_ms'])
            if ratios:
                avg_ratio = sum(ratios) / len(ratios)
                if avg_ratio < 0.7:
                    # Very early braking — large penalty
                    entry_score -= PENALTY_EARLY_BRAKE * 2
                elif avg_ratio < 0.85:
                    # Early braking
                    entry_score -= PENALTY_EARLY_BRAKE
                elif avg_ratio > 1.1:
                    # Late braking (carrying too much speed)
                    entry_score -= PENALTY_LATE_BRAKE

        # --- Apex score: based on lateral offset at apex ---
        apex_score = 100
        # Use apex frames, or middle third of corner as proxy
        apex_region = apex_frames if apex_frames else []
        if not apex_region:
            third = len(cframes) // 3
            apex_region = cframes[third:2 * third] if third > 0 else cframes

        if apex_region:
            laterals = [abs(f['lateral_offset']) for f in apex_region]
            mean_lateral = sum(laterals) / len(laterals)
            # Proportional penalty: 2m=0, 4m=-10, 6m=-20
            if mean_lateral > APEX_LATERAL_THRESHOLD:
                penalty = min(PENALTY_MISSED_APEX, int((mean_lateral - APEX_LATERAL_THRESHOLD) * 10))
                apex_score -= penalty

        # --- Exit score: speed recovery + throttle application ---
        exit_score = 100
        if exit_frames:
            # Check speed ratio at exit
            ratios = []
            low_throttle_pct = 0
            for f in exit_frames:
                if f['target_speed_ms'] > 1:
                    ratios.append(f['player_speed_ms'] / f['target_speed_ms'])
                if f['throttle'] < EXIT_THROTTLE_THRESHOLD:
                    low_throttle_pct += 1

            low_throttle_pct = low_throttle_pct / len(exit_frames)
            if ratios:
                avg_ratio = sum(ratios) / len(ratios)
                if avg_ratio < 0.7 and low_throttle_pct > 0.5:
                    exit_score -= PENALTY_POOR_EXIT
                elif avg_ratio < 0.85 and low_throttle_pct > 0.3:
                    exit_score -= int(PENALTY_POOR_EXIT * 0.6)

        # Clamp
        entry_score = max(0, entry_score)
        apex_score = max(0, apex_score)
        exit_score = max(0, exit_score)

        # Aggregate metrics
        all_deltas = [f['speed_delta'] for f in cframes]
        avg_speed_delta = sum(all_deltas) / len(all_deltas) if all_deltas else 0
        max_lateral_error = max((abs(f['lateral_offset']) for f in cframes), default=0)

        # Per-phase metrics for coaching layer
        entry_deltas = [f['speed_delta'] for f in entry_frames]
        avg_entry_speed_delta = sum(entry_deltas) / len(entry_deltas) if entry_deltas else 0

        apex_laterals = [f['lateral_offset'] for f in apex_region]
        avg_apex_lateral = sum(apex_laterals) / len(apex_laterals) if apex_laterals else 0

        exit_deltas = [f['speed_delta'] for f in exit_frames]
        avg_exit_speed_delta = sum(exit_deltas) / len(exit_deltas) if exit_deltas else 0

        exit_throttles = [f['throttle'] for f in exit_frames]
        avg_exit_throttle = sum(exit_throttles) / len(exit_throttles) if exit_throttles else 1.0

        # Time to 80% throttle: per-pass, then average
        # Group exit frames by lap to compute per-pass
        exit_by_lap = defaultdict(list)
        for f in exit_frames:
            exit_by_lap[f['lap_number']].append(f)

        t80_values = []
        for lap_frames in exit_by_lap.values():
            if not lap_frames:
                continue
            t_start = lap_frames[0]['session_time']
            for f in lap_frames:
                if f['throttle'] >= 0.8:
                    t80_values.append(f['session_time'] - t_start)
                    break

        avg_time_to_80 = sum(t80_values) / len(t80_values) if t80_values else -1.0

        corner_results.append({
            'corner_id': cid,
            'entry_score': entry_score,
            'apex_score': apex_score,
            'exit_score': exit_score,
            'avg_speed_delta': round(avg_speed_delta, 2),
            'max_lateral_error': round(max_lateral_error, 2),
            'avg_entry_speed_delta': round(avg_entry_speed_delta, 2),
            'avg_apex_lateral': round(avg_apex_lateral, 2),
            'avg_exit_speed_delta': round(avg_exit_speed_delta, 2),
            'avg_exit_throttle': round(avg_exit_throttle, 3),
            'time_to_80_throttle': round(avg_time_to_80, 3),
            'frames': len(cframes),
            'entry_frames': len(entry_frames),
            'apex_frames': len(apex_frames),
            'exit_frames': len(exit_frames),
        })

    # Summary
    print("\n" + "=" * 60)
    print("Corner Analysis Results")
    print("=" * 60)
    print(f"{'ID':>3} {'Entry':>6} {'Apex':>6} {'Exit':>6} {'AvgΔv':>8} {'MaxLat':>7} {'Frames':>7}")
    print("-" * 60)

    all_scores = []
    for cr in corner_results:
        print(f"{cr['corner_id']:>3} "
              f"{cr['entry_score']:>6} "
              f"{cr['apex_score']:>6} "
              f"{cr['exit_score']:>6} "
              f"{cr['avg_speed_delta']:>+7.1f} "
              f"{cr['max_lateral_error']:>7.1f} "
              f"{cr['frames']:>7}")
        all_scores.extend([cr['entry_score'], cr['apex_score'], cr['exit_score']])

    print("-" * 60)
    if corner_results:
        avg_entry = sum(c['entry_score'] for c in corner_results) / len(corner_results)
        avg_apex = sum(c['apex_score'] for c in corner_results) / len(corner_results)
        avg_exit = sum(c['exit_score'] for c in corner_results) / len(corner_results)
        overall = (avg_entry + avg_apex + avg_exit) / 3
        print(f"AVG {avg_entry:>6.0f} {avg_apex:>6.0f} {avg_exit:>6.0f}   Overall: {overall:.0f}/100")

    # Validation
    print("\nValidation:")
    all_laterals = [abs(f['lateral_offset']) for f in frame_data]
    print(f"  Lateral offset: mean={sum(all_laterals)/len(all_laterals):.1f}m, "
          f"max={max(all_laterals):.1f}m")
    print(f"  Index jumps: {jumps}")
    score_set = set(all_scores)
    if len(score_set) == 1:
        print(f"  WARNING: All scores identical ({score_set.pop()}) — may need tuning")
    else:
        print(f"  Score distribution: {len([s for s in all_scores if s == 100])} perfect, "
              f"{len([s for s in all_scores if s < 100])} penalized")

    # Convert corner_targets keys to strings for JSON
    corner_targets_json = {str(k): v for k, v in corner_targets.items()}

    return {
        'track_id': intel.get('track_id'),
        'telemetry_file': os.path.basename(telemetry_path),
        'total_frames': len(frames),
        'valid_frames': len(valid_frames),
        'corners_analyzed': len(corner_results),
        'corner_targets': corner_targets_json,
        'corners': corner_results,
    }


# ─── CLI ─────────────────────────────────────────────────────────────────────

def main():
    output_path = None
    intel_path = None
    telemetry_path = None

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
            if intel_path is None:
                intel_path = args[i]
            elif telemetry_path is None:
                telemetry_path = args[i]
            i += 1

    if not intel_path or not telemetry_path:
        print("F1 2025 Player vs Track Analysis")
        print("=" * 40)
        print()
        print("Usage: python3 driver_analysis.py <intelligence.json> <telemetry.jsonl> [-o output.json]")
        print()
        print("Evaluates driver performance against the track intelligence model.")
        print()
        print("Examples:")
        print('  python3 driver_analysis.py "Track Map Builds/track_0_intelligence.json" telemetry/session.jsonl')
        print('  python3 driver_analysis.py intel.json telemetry.jsonl -o my_analysis.json')
        sys.exit(1)

    print("F1 2025 Player vs Track Analysis")
    print("=" * 40)

    result = analyze(intel_path, telemetry_path)

    if result:
        MAP_OUTPUT_DIR = "Track Map Builds"
        os.makedirs(MAP_OUTPUT_DIR, exist_ok=True)
        if output_path is None:
            track_id = result.get('track_id')
            track_name = f"track_{track_id}" if track_id is not None else "track_unknown"
            output_path = os.path.join(MAP_OUTPUT_DIR, f"{track_name}_driver_analysis.json")

        with open(output_path, 'w') as f:
            json.dump(result, f, indent=2)

        print(f"\nDriver analysis written to {output_path}")


if __name__ == '__main__':
    main()
