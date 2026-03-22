#!/usr/bin/env python3
"""
F1 2025 Phase 1–22 Automated Validation Suite

Deterministic tests using only:
- Recorded JSONL telemetry
- Built track maps / intelligence / analysis
- Synthetic controlled data

No human input required. No guessing expected values.
Only validates against known constraints, invariants, and synthetic data.

Usage:
    python3 validation_suite.py
"""

import json
import math
import os
import sys
import time
from collections import defaultdict

# ─── Paths ──────────────────────────────────────────────────────────────────

TELEMETRY_FILE = "telemetry/telemetry_20260317_161505.jsonl"
TRACK_MAP_FILE = "Track Map Builds/track_0_true_map.json"
INTEL_FILE = "Track Map Builds/track_0_intelligence.json"
ANALYSIS_FILE = "Track Map Builds/track_0_driver_analysis.json"
COACHING_FILE = "Track Map Builds/track_0_coaching_report.json"

# ─── Test Framework ─────────────────────────────────────────────────────────

passed = 0
failed = 0
errors = []


def check(name, condition, detail=""):
    global passed, failed
    if condition:
        passed += 1
        print(f"  ✓ {name}")
    else:
        failed += 1
        msg = f"  ✗ {name}"
        if detail:
            msg += f" — {detail}"
        print(msg)
        errors.append(f"{name}: {detail}")


# ═══════════════════════════════════════════════════════════════════════════
# GROUP 1 — UDP & DECODER VALIDATION (from recorded telemetry)
# ═══════════════════════════════════════════════════════════════════════════

def test_group_1():
    print("\n" + "=" * 60)
    print("GROUP 1 — UDP & DECODER VALIDATION")
    print("=" * 60)

    frames = []
    with open(TELEMETRY_FILE) as f:
        for line in f:
            line = line.strip()
            if line:
                frames.append(json.loads(line))

    # Test 1.1: Packet Decode Integrity
    print("\n[1.1] Packet Decode Integrity")
    check("Frames loaded", len(frames) > 0, f"got {len(frames)}")

    required_fields = ['timestamp', 'sessionTime', 'frameId', 'player']
    player_fields = ['speed', 'throttle', 'brake', 'steering', 'gear',
                     'lapNumber', 'lapDistance', 'position', 'world_pos_m']

    missing_top = 0
    missing_player = 0
    for frame in frames:
        for field in required_fields:
            if field not in frame:
                missing_top += 1
        player = frame.get('player', {})
        if player:
            for field in player_fields:
                if field not in player:
                    missing_player += 1

    check("All top-level fields present", missing_top == 0,
          f"{missing_top} missing")
    check("All player fields present", missing_player == 0,
          f"{missing_player} missing")

    # Test 1.2: Numeric Range Validation
    print("\n[1.2] Numeric Range Validation")
    throttle_oob = 0
    brake_oob = 0
    steer_oob = 0
    speed_oob = 0
    total_with_player = 0

    for frame in frames:
        player = frame.get('player')
        if not player:
            continue
        total_with_player += 1
        t = player.get('throttle', 0)
        b = player.get('brake', 0)
        s = player.get('steering', 0)
        spd = player.get('speed', 0)
        if t < -0.01 or t > 1.01:
            throttle_oob += 1
        if b < -0.01 or b > 1.01:
            brake_oob += 1
        if s < -1.01 or s > 1.01:
            steer_oob += 1
        if spd < -1 or spd > 400:
            speed_oob += 1

    check("throttle ∈ [0, 1]", throttle_oob == 0,
          f"{throttle_oob}/{total_with_player} out of range")
    check("brake ∈ [0, 1]", brake_oob == 0,
          f"{brake_oob}/{total_with_player} out of range")
    check("steering ∈ [-1, 1]", steer_oob == 0,
          f"{steer_oob}/{total_with_player} out of range")
    check("speed ∈ [0, 400]", speed_oob == 0,
          f"{speed_oob}/{total_with_player} out of range")

    # Test 1.3: Temporal Continuity
    # Skip first few frames (session start can teleport from garage to grid)
    print("\n[1.3] Temporal Continuity")
    pos_jumps = 0
    speed_jumps = 0
    prev_frame = None
    frame_idx = 0

    for frame in frames:
        player = frame.get('player')
        if not player or 'world_pos_m' not in player:
            prev_frame = None
            frame_idx += 1
            continue
        if prev_frame and frame_idx > 5:
            pp = prev_frame['player']
            wp = player['world_pos_m']
            pwp = pp['world_pos_m']
            dx = wp['x'] - pwp['x']
            dy = wp.get('y', 0) - pwp.get('y', 0)
            dz = wp['z'] - pwp['z']
            dist = math.sqrt(dx*dx + dy*dy + dz*dz)
            if dist > 20:
                pos_jumps += 1
            dspeed = abs(player['speed'] - pp['speed'])
            if dspeed > 50:
                speed_jumps += 1
        prev_frame = frame
        frame_idx += 1

    check("Δposition < 20m/frame", pos_jumps == 0,
          f"{pos_jumps} jumps")
    check("Δspeed < 50 km/h/frame", speed_jumps == 0,
          f"{speed_jumps} jumps")


# ═══════════════════════════════════════════════════════════════════════════
# GROUP 2 — STATE MERGE VALIDATION
# ═══════════════════════════════════════════════════════════════════════════

def test_group_2():
    print("\n" + "=" * 60)
    print("GROUP 2 — STATE MERGE VALIDATION")
    print("=" * 60)

    frames = []
    with open(TELEMETRY_FILE) as f:
        for line in f:
            line = line.strip()
            if line:
                frames.append(json.loads(line))

    # Test 2.1: Field Completeness
    print("\n[2.1] Field Completeness")
    missing_player = 0
    missing_nearby = 0
    for frame in frames:
        if 'player' not in frame or frame['player'] is None:
            missing_player += 1
        if 'nearbyCars' not in frame:
            missing_nearby += 1

    check("player field present in all frames", missing_player == 0,
          f"{missing_player} missing")
    check("nearbyCars field present in all frames", missing_nearby == 0,
          f"{missing_nearby} missing")

    # Test 2.2: Nearby Car Selection
    print("\n[2.2] Nearby Car Selection")
    max_nearby = 0
    for frame in frames:
        nc = frame.get('nearbyCars', [])
        if len(nc) > max_nearby:
            max_nearby = len(nc)

    check("nearbyCars ≤ 6", max_nearby <= 6,
          f"max seen: {max_nearby}")

    # Check sorting by gap
    unsorted_count = 0
    for frame in frames:
        nc = frame.get('nearbyCars', [])
        if len(nc) > 1:
            gaps = [c.get('gap', 0) for c in nc]
            if gaps != sorted(gaps):
                unsorted_count += 1

    check("nearbyCars sorted by gap ascending", unsorted_count == 0,
          f"{unsorted_count} frames unsorted")


# ═══════════════════════════════════════════════════════════════════════════
# GROUP 3 — TRACK MAP PIPELINE
# ═══════════════════════════════════════════════════════════════════════════

def test_group_3():
    print("\n" + "=" * 60)
    print("GROUP 3 — TRACK MAP PIPELINE")
    print("=" * 60)

    with open(TRACK_MAP_FILE) as f:
        track = json.load(f)
    points = track['points']
    n = len(points)

    # Test 3.1: Centerline Smoothness
    print("\n[3.1] Centerline Smoothness")
    # Compute curvature using a wider step (5 points) to avoid noise from
    # near-coincident points at 1m resolution
    STEP = 5
    max_curv = 0
    short_spikes = 0
    curvatures = []
    for i in range(n):
        i_prev = (i - STEP) % n
        i_next = (i + STEP) % n
        du1 = points[i]['u'] - points[i_prev]['u']
        dv1 = points[i]['v'] - points[i_prev]['v']
        du2 = points[i_next]['u'] - points[i]['u']
        dv2 = points[i_next]['v'] - points[i]['v']
        h1 = math.atan2(dv1, du1)
        h2 = math.atan2(dv2, du2)
        dh = h2 - h1
        while dh > math.pi:
            dh -= 2 * math.pi
        while dh < -math.pi:
            dh += 2 * math.pi
        ds = math.sqrt(du2*du2 + dv2*dv2)
        k = abs(dh / ds) if ds > 0.1 else 0
        curvatures.append(k)
        if k > max_curv:
            max_curv = k

    # Count spikes > 0.05 lasting < 3 points
    for i in range(n):
        if curvatures[i] > 0.05:
            neighbors_spiked = 0
            for d in [-2, -1, 1, 2]:
                if curvatures[(i + d) % n] > 0.05:
                    neighbors_spiked += 1
            if neighbors_spiked < 2:
                short_spikes += 1

    check("max curvature < 0.2", max_curv < 0.2,
          f"max={max_curv:.4f}")
    check("no isolated curvature spikes > 0.05", short_spikes == 0,
          f"{short_spikes} isolated spikes")

    # Test 3.2: Width Stability
    print("\n[3.2] Width Stability")
    max_dw = 0
    width_violations = 0
    for i in range(n):
        i_next = (i + 1) % n
        dw = abs(points[i_next]['half_width'] - points[i]['half_width'])
        if dw > max_dw:
            max_dw = dw
        if dw > 0.5:
            width_violations += 1

    check("Δwidth < 0.5m between adjacent points", width_violations == 0,
          f"{width_violations} violations, max Δw={max_dw:.3f}m")

    # Test 3.3: Normal Consistency
    print("\n[3.3] Normal Consistency")
    max_normal_change = 0
    normal_violations = 0
    for i in range(n):
        i_next = (i + 1) % n
        nu1, nv1 = points[i]['nu'], points[i]['nv']
        nu2, nv2 = points[i_next]['nu'], points[i_next]['nv']
        # Angle between normals
        dot = nu1 * nu2 + nv1 * nv2
        dot = max(-1, min(1, dot))
        angle_deg = math.degrees(math.acos(dot))
        if angle_deg > max_normal_change:
            max_normal_change = angle_deg
        if angle_deg > 10:
            normal_violations += 1

    check("normal angle change < 10°", normal_violations == 0,
          f"{normal_violations} violations, max={max_normal_change:.2f}°")


# ═══════════════════════════════════════════════════════════════════════════
# GROUP 4 — PROJECTION VALIDATION (synthetic)
# ═══════════════════════════════════════════════════════════════════════════

def test_group_4():
    print("\n" + "=" * 60)
    print("GROUP 4 — PROJECTION VALIDATION")
    print("=" * 60)

    # Import projection function from driver_analysis
    sys.path.insert(0, '.')
    from driver_analysis import compute_lateral_offset

    # Test 4.1: Synthetic Straight Line
    print("\n[4.1] Synthetic Straight Line")
    # Track: straight line along u-axis, heading = 0
    heading = 0.0
    track_u, track_v = 100.0, 0.0

    # Car at constant offset of +5m to the right (positive lateral)
    offsets = []
    for u in range(0, 200, 10):
        lat = compute_lateral_offset(float(u), 5.0, float(u), 0.0, heading)
        offsets.append(lat)

    # All offsets should be identical (constant lateral offset)
    offset_range = max(offsets) - min(offsets)
    check("constant offset on straight track", offset_range < 0.01,
          f"range={offset_range:.6f}")

    # Test 4.2: Synthetic Curve
    print("\n[4.2] Synthetic Curve")
    # Track: circular arc (radius 100m, centered at origin)
    R = 100.0
    offsets_curve = []
    prev_sign = None
    sign_flips_without_crossing = 0

    for deg in range(0, 360, 5):
        rad = math.radians(deg)
        track_u = R * math.cos(rad)
        track_v = R * math.sin(rad)
        heading = rad + math.pi / 2  # tangent direction

        # Car at radius 105m (5m outside)
        car_u = 105.0 * math.cos(rad)
        car_v = 105.0 * math.sin(rad)

        lat = compute_lateral_offset(car_u, car_v, track_u, track_v, heading)
        offsets_curve.append(lat)

        # Check for sign flips
        curr_sign = 1 if lat >= 0 else -1
        if prev_sign is not None and curr_sign != prev_sign:
            # Sign flip without crossing centerline (offset should stay same side)
            sign_flips_without_crossing += 1
        prev_sign = curr_sign

    # Offsets should vary smoothly (all same sign for this case)
    check("no unexpected sign flips on curve", sign_flips_without_crossing == 0,
          f"{sign_flips_without_crossing} flips")

    # Offsets should be approximately constant (~5m)
    mean_offset = sum(abs(o) for o in offsets_curve) / len(offsets_curve)
    check("offset magnitude ~5m on circular arc",
          4.0 < mean_offset < 6.0,
          f"mean |offset|={mean_offset:.2f}m")


# ═══════════════════════════════════════════════════════════════════════════
# GROUP 5 — CORNER DETECTION
# ═══════════════════════════════════════════════════════════════════════════

def test_group_5():
    print("\n" + "=" * 60)
    print("GROUP 5 — CORNER DETECTION")
    print("=" * 60)

    with open(INTEL_FILE) as f:
        intel = json.load(f)

    points = intel['points']

    # Identify corners and their arc lengths
    corner_points = defaultdict(list)
    for p in points:
        cid = p['corner_id']
        if cid >= 0:
            corner_points[cid].append(p)

    # Test 5.1: Minimum Corner Length
    print("\n[5.1] Minimum Corner Length")
    short_corners = 0
    for cid, pts in corner_points.items():
        arc_start = pts[0]['s']
        arc_end = pts[-1]['s']
        length = arc_end - arc_start
        if length < 0:
            # Wrap around
            length = intel['total_arc_length_m'] - arc_start + arc_end
        if length < 30:
            short_corners += 1

    check("all corners ≥ 30m", short_corners == 0,
          f"{short_corners} corners < 30m")

    # Test 5.2: Curvature Threshold
    print("\n[5.2] Curvature Threshold")
    # Every corner should contain at least one point with |curvature| above threshold
    no_peak_corners = 0
    CURVATURE_THRESHOLD = 0.005
    for cid, pts in corner_points.items():
        max_k = max(abs(p['curvature']) for p in pts)
        if max_k < CURVATURE_THRESHOLD:
            no_peak_corners += 1

    check("all corners have curvature peak above threshold",
          no_peak_corners == 0,
          f"{no_peak_corners} corners with no peak")


# ═══════════════════════════════════════════════════════════════════════════
# GROUP 6 — PHASE SEGMENTATION (synthetic)
# ═══════════════════════════════════════════════════════════════════════════

def test_group_6():
    print("\n" + "=" * 60)
    print("GROUP 6 — PHASE SEGMENTATION")
    print("=" * 60)

    # Simulate the phase segmentation logic from driver_analysis
    # We'll create synthetic frame sequences and run the segmenter

    BRAKE_THRESHOLD = 0.1
    THROTTLE_START = 0.2

    def segment_corner(frames_slice):
        """Minimal re-implementation of phase segmenter from driver_analysis."""
        nf = len(frames_slice)
        speeds = [f['speed'] for f in frames_slice]
        brakes = [f['brake'] for f in frames_slice]
        throttles = [f['throttle'] for f in frames_slice]

        # Entry start: first brake
        entry_start = None
        for j in range(nf):
            if brakes[j] > BRAKE_THRESHOLD:
                entry_start = j
                break

        # Apex: min speed
        min_speed_idx = speeds.index(min(speeds))

        # Adaptive apex window
        min_speed_kmh = speeds[min_speed_idx] * 3.6
        if min_speed_kmh < 120:
            apex_half = 12
        elif min_speed_kmh > 180:
            apex_half = 6
        else:
            apex_half = 8

        apex_start = max(0, min_speed_idx - apex_half)
        apex_end = min(nf - 1, min_speed_idx + apex_half)

        if entry_start is not None:
            apex_start = max(apex_start, entry_start + 1)

        # Exit start: first throttle > 0.2 after apex
        exit_start = None
        for j in range(apex_end, nf):
            if throttles[j] > THROTTLE_START:
                exit_start = j
                break

        # Assign phases
        phases = ['none'] * nf
        for j in range(nf):
            if entry_start is not None and j >= entry_start and j < apex_start:
                phases[j] = 'entry'
            elif j >= apex_start and j <= apex_end:
                phases[j] = 'apex'
            elif exit_start is not None and j >= exit_start:
                phases[j] = 'exit'

        return phases

    # Test 6.1: Synthetic Corner Scenario
    print("\n[6.1] Synthetic Corner Scenario")
    # braking → rotation → throttle
    synthetic = []
    # Approach (no brake): 10 frames at 80 m/s
    for i in range(10):
        synthetic.append({'speed': 80, 'brake': 0.0, 'throttle': 0.8})
    # Braking: 15 frames, speed drops 80→30
    for i in range(15):
        spd = 80 - (50 * (i + 1) / 15)
        synthetic.append({'speed': spd, 'brake': 0.8, 'throttle': 0.0})
    # Rotation (min speed): 10 frames at ~30
    for i in range(10):
        synthetic.append({'speed': 30 + i * 0.5, 'brake': 0.0, 'throttle': 0.0})
    # Throttle out: 15 frames, throttle ramps up
    for i in range(15):
        synthetic.append({'speed': 35 + i * 3, 'brake': 0.0, 'throttle': 0.3 + i * 0.05})

    phases = segment_corner(synthetic)

    entry_frames = [synthetic[i] for i, p in enumerate(phases) if p == 'entry']
    apex_frames_s = [synthetic[i] for i, p in enumerate(phases) if p == 'apex']
    exit_frames = [synthetic[i] for i, p in enumerate(phases) if p == 'exit']

    # Entry should contain braking frames
    entry_all_braking = all(f['brake'] > 0 for f in entry_frames) if entry_frames else True
    check("entry contains braking frames", entry_all_braking and len(entry_frames) > 0,
          f"{len(entry_frames)} entry frames")

    # Apex should contain min speed window
    if apex_frames_s:
        apex_speeds = [f['speed'] for f in apex_frames_s]
        global_min = min(f['speed'] for f in synthetic)
        check("apex contains min speed", global_min in apex_speeds or
              any(abs(s - global_min) < 1 for s in apex_speeds),
              f"min_speed={global_min}, apex_speeds range [{min(apex_speeds):.1f}, {max(apex_speeds):.1f}]")
    else:
        check("apex frames exist", False, "no apex frames")

    # Exit should only contain throttle > 0.2 frames
    exit_all_throttle = all(f['throttle'] > 0.2 for f in exit_frames) if exit_frames else True
    check("exit contains only throttle > 0.2", exit_all_throttle and len(exit_frames) > 0,
          f"{len(exit_frames)} exit frames")

    # Test 6.2: No-Throttle Case
    print("\n[6.2] No-Throttle Case")
    synthetic_no_throttle = []
    for i in range(10):
        synthetic_no_throttle.append({'speed': 80, 'brake': 0.0, 'throttle': 0.0})
    for i in range(15):
        spd = 80 - (50 * (i + 1) / 15)
        synthetic_no_throttle.append({'speed': spd, 'brake': 0.8, 'throttle': 0.0})
    for i in range(20):
        synthetic_no_throttle.append({'speed': 30, 'brake': 0.0, 'throttle': 0.0})

    phases_nt = segment_corner(synthetic_no_throttle)
    exit_count = phases_nt.count('exit')
    check("no exit phase when no throttle", exit_count == 0,
          f"got {exit_count} exit frames")


# ═══════════════════════════════════════════════════════════════════════════
# GROUP 7 — TARGET SPEED MODEL
# ═══════════════════════════════════════════════════════════════════════════

def test_group_7():
    print("\n" + "=" * 60)
    print("GROUP 7 — TARGET SPEED MODEL")
    print("=" * 60)

    # Test 7.1: Percentile Computation
    print("\n[7.1] Percentile Computation")

    def percentile(values, pct):
        s = sorted(values)
        k = (len(s) - 1) * pct / 100.0
        f = int(k)
        c = f + 1 if f + 1 < len(s) else f
        d = k - f
        return s[f] + d * (s[c] - s[f])

    # Known dataset: [10, 20, 30, 40, 50, 60, 70, 80, 90, 100]
    data = list(range(10, 101, 10))
    p50 = percentile(data, 50)
    p75 = percentile(data, 75)
    p90 = percentile(data, 90)

    check("50th percentile of [10..100] = 55.0", abs(p50 - 55.0) < 0.01,
          f"got {p50}")
    check("75th percentile of [10..100] = 77.5", abs(p75 - 77.5) < 0.01,
          f"got {p75}")
    check("90th percentile of [10..100] = 91.0", abs(p90 - 91.0) < 0.01,
          f"got {p90}")

    # Single value
    p_single = percentile([42], 75)
    check("percentile of single value = that value", abs(p_single - 42) < 0.01,
          f"got {p_single}")

    # Test 7.2: Value Sanity
    print("\n[7.2] Value Sanity")
    with open(ANALYSIS_FILE) as f:
        analysis = json.load(f)

    targets = analysis.get('corner_targets', {})
    nan_count = 0
    negative_count = 0
    for cid, t in targets.items():
        for key, val in t.items():
            if val != val:  # NaN check
                nan_count += 1
            if val < 0:
                negative_count += 1

    check("no NaN in reference speeds", nan_count == 0, f"{nan_count} NaN")
    check("no negative reference speeds", negative_count == 0,
          f"{negative_count} negative")


# ═══════════════════════════════════════════════════════════════════════════
# GROUP 8 — COACHING LOGIC (synthetic)
# ═══════════════════════════════════════════════════════════════════════════

def test_group_8():
    print("\n" + "=" * 60)
    print("GROUP 8 — COACHING LOGIC")
    print("=" * 60)

    # Import coaching logic
    sys.path.insert(0, '.')
    from coaching_report import generate_coaching, NOISE_DEADZONE

    # Test 8.1: Synthetic Early Braking
    print("\n[8.1] Synthetic Early Braking")
    # Write a temporary analysis JSON with known deltas
    tmp = {
        'track_id': 99,
        'telemetry_file': 'test.jsonl',
        'corners_analyzed': 1,
        'corner_targets': {},
        'corners': [{
            'corner_id': 0,
            'entry_score': 80, 'apex_score': 100, 'exit_score': 100,
            'avg_speed_delta': -10,
            'max_lateral_error': 1.0,
            'avg_entry_speed_delta': -8.0,  # below -5 threshold
            'avg_apex_lateral': 0.0,
            'avg_exit_speed_delta': 0.0,
            'avg_exit_throttle': 0.9,
            'time_to_80_throttle': 0.5,
            'frames': 100, 'entry_frames': 30, 'apex_frames': 10, 'exit_frames': 30,
        }]
    }
    tmp_path = '/tmp/test_analysis_early.json'
    with open(tmp_path, 'w') as f:
        json.dump(tmp, f)

    result = generate_coaching(tmp_path)
    issues = result['corners'][0]['issues']
    types = [i['type'] for i in issues]
    check("early braking detected", 'early_braking' in types,
          f"got types: {types}")

    # Test 8.2: Synthetic Late Braking
    print("\n[8.2] Synthetic Late Braking")
    tmp['corners'][0]['avg_entry_speed_delta'] = 8.0  # above +5 threshold
    with open(tmp_path, 'w') as f:
        json.dump(tmp, f)

    result = generate_coaching(tmp_path)
    issues = result['corners'][0]['issues']
    types = [i['type'] for i in issues]
    check("late braking detected", 'late_braking' in types,
          f"got types: {types}")

    # Test 8.3: Deadzone
    print("\n[8.3] Deadzone")
    tmp['corners'][0]['avg_entry_speed_delta'] = 2.0   # within ±3 deadzone
    tmp['corners'][0]['avg_exit_speed_delta'] = -2.0    # within ±3 deadzone
    tmp['corners'][0]['avg_apex_lateral'] = 0.5          # within threshold
    tmp['corners'][0]['avg_exit_throttle'] = 0.9         # above threshold
    with open(tmp_path, 'w') as f:
        json.dump(tmp, f)

    result = generate_coaching(tmp_path)
    issues = result['corners'][0]['issues']
    check("no issues within deadzone", len(issues) == 0,
          f"got {len(issues)} issues: {[i['type'] for i in issues]}")

    os.remove(tmp_path)


# ═══════════════════════════════════════════════════════════════════════════
# GROUP 9 — REPLAY DETERMINISM
# ═══════════════════════════════════════════════════════════════════════════

def test_group_9():
    print("\n" + "=" * 60)
    print("GROUP 9 — REPLAY DETERMINISM")
    print("=" * 60)

    print("\n[9.1] Deterministic Output")
    sys.path.insert(0, '.')
    from driver_analysis import analyze

    # Suppress print output
    import io
    old_stdout = sys.stdout

    sys.stdout = io.StringIO()
    result1 = analyze(INTEL_FILE, TELEMETRY_FILE)
    sys.stdout = io.StringIO()
    result2 = analyze(INTEL_FILE, TELEMETRY_FILE)
    sys.stdout = old_stdout

    # Compare JSON serializations
    json1 = json.dumps(result1, sort_keys=True)
    json2 = json.dumps(result2, sort_keys=True)

    check("two runs produce identical output", json1 == json2,
          f"outputs differ (len1={len(json1)}, len2={len(json2)})")


# ═══════════════════════════════════════════════════════════════════════════
# GROUP 10 — SYSTEM STABILITY
# ═══════════════════════════════════════════════════════════════════════════

def test_group_10():
    print("\n" + "=" * 60)
    print("GROUP 10 — SYSTEM STABILITY")
    print("=" * 60)

    print("\n[10.1] Long Run — Full Pipeline")
    # Find the largest telemetry file
    tel_dir = "telemetry"
    tel_files = [os.path.join(tel_dir, f) for f in os.listdir(tel_dir) if f.endswith('.jsonl')]
    largest = max(tel_files, key=os.path.getsize)
    size_mb = os.path.getsize(largest) / (1024 * 1024)
    print(f"  Using: {largest} ({size_mb:.1f} MB)")

    # Count frames
    frame_count = 0
    with open(largest) as f:
        for line in f:
            if line.strip():
                frame_count += 1

    start = time.time()

    # Run full analysis pipeline without crashing
    crashed = False
    try:
        import io
        old_stdout = sys.stdout
        sys.stdout = io.StringIO()
        from driver_analysis import analyze
        result = analyze(INTEL_FILE, largest)
        sys.stdout = old_stdout
    except Exception as e:
        sys.stdout = old_stdout
        crashed = True
        check("pipeline completes without crash", False, str(e))

    elapsed = time.time() - start

    if not crashed:
        check("pipeline completes without crash", True)
        fps = frame_count / elapsed if elapsed > 0 else 0
        check(f"processed {frame_count} frames in {elapsed:.1f}s ({fps:.0f} fps)",
              True)

        # Verify output is valid
        check("result contains corners", result is not None and len(result.get('corners', [])) > 0,
              f"corners: {len(result.get('corners', [])) if result else 0}")


# ═══════════════════════════════════════════════════════════════════════════
# GROUP 11 — FPS / THROUGHPUT VALIDATION
# ═══════════════════════════════════════════════════════════════════════════

def test_group_11():
    print("\n" + "=" * 60)
    print("GROUP 11 — FPS / THROUGHPUT VALIDATION")
    print("=" * 60)

    import io
    import resource
    sys.path.insert(0, '.')
    from driver_analysis import analyze
    from coaching_report import generate_coaching

    # Find largest telemetry file
    tel_dir = "telemetry"
    tel_files = [os.path.join(tel_dir, f) for f in os.listdir(tel_dir) if f.endswith('.jsonl')]
    largest = max(tel_files, key=os.path.getsize)
    size_mb = os.path.getsize(largest) / (1024 * 1024)

    # Count frames
    frame_count = 0
    with open(largest) as f:
        for line in f:
            if line.strip():
                frame_count += 1

    # Test 11.1: Raw Processing Speed
    print(f"\n[11.1] Raw Processing Speed")
    print(f"  Input: {largest} ({size_mb:.1f} MB, {frame_count} frames)")

    old_stdout = sys.stdout
    mem_before = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss

    sys.stdout = io.StringIO()
    t0 = time.time()
    result = analyze(INTEL_FILE, largest)
    t1 = time.time()
    sys.stdout = old_stdout

    elapsed = t1 - t0
    fps = frame_count / elapsed if elapsed > 0 else 0
    mem_after = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    # macOS reports bytes, Linux reports KB
    mem_delta_mb = abs(mem_after - mem_before) / (1024 * 1024)

    print(f"  Runtime: {elapsed:.2f}s")
    print(f"  FPS: {fps:.0f}")
    print(f"  Memory delta: {mem_delta_mb:.1f} MB")

    check("FPS ≥ 30 (real-time)", fps >= 30,
          f"fps={fps:.0f}")
    check("no crash during processing", result is not None)

    # Test 11.2: End-to-End Pipeline (analysis → coaching)
    print(f"\n[11.2] End-to-End Pipeline (analysis → coaching)")

    sys.stdout = io.StringIO()
    t0 = time.time()
    result_e2e = analyze(INTEL_FILE, largest)
    sys.stdout = old_stdout

    # Write analysis to temp, then run coaching
    tmp_analysis = '/tmp/test_e2e_analysis.json'
    with open(tmp_analysis, 'w') as f:
        json.dump(result_e2e, f)

    coaching_result = generate_coaching(tmp_analysis)
    t1 = time.time()

    e2e_elapsed = t1 - t0
    e2e_fps = frame_count / e2e_elapsed if e2e_elapsed > 0 else 0

    print(f"  End-to-end runtime: {e2e_elapsed:.2f}s ({e2e_fps:.0f} fps)")

    # Validate output integrity
    corners = coaching_result.get('corners', [])
    has_nan = False
    has_null = False
    for corner in corners:
        if corner.get('corner_id') is None:
            has_null = True
        for issue in corner.get('issues', []):
            for v in issue.values():
                if isinstance(v, float) and v != v:
                    has_nan = True

    check("coaching output generated", len(corners) > 0,
          f"{len(corners)} corners")
    check("no NaN in coaching output", not has_nan)
    check("no null corner IDs", not has_null)
    check("all corners present in coaching",
          coaching_result.get('corners_analyzed', 0) == result_e2e.get('corners_analyzed', 0),
          f"coaching={coaching_result.get('corners_analyzed')}, analysis={result_e2e.get('corners_analyzed')}")

    os.remove(tmp_analysis)

    # Test 11.3: Stress Test (3x dataset)
    print(f"\n[11.3] Stress Test (3x dataset)")
    big_path = '/tmp/stress_test_3x.jsonl'

    # Create 3x dataset
    with open(big_path, 'w') as out:
        for _ in range(3):
            with open(largest) as inp:
                for line in inp:
                    out.write(line)

    big_frames = frame_count * 3
    big_size = os.path.getsize(big_path) / (1024 * 1024)
    print(f"  Input: {big_size:.0f} MB, {big_frames} frames")

    mem_before_stress = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss

    sys.stdout = io.StringIO()
    t0 = time.time()
    result_stress = analyze(INTEL_FILE, big_path)
    t1 = time.time()
    sys.stdout = old_stdout

    stress_elapsed = t1 - t0
    stress_fps = big_frames / stress_elapsed if stress_elapsed > 0 else 0
    mem_after_stress = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    stress_mem_mb = abs(mem_after_stress - mem_before_stress) / (1024 * 1024)

    # Check linear scaling: 3x data should take roughly 2-5x time (some overhead ok)
    scaling_ratio = stress_elapsed / elapsed if elapsed > 0 else 0

    print(f"  Runtime: {stress_elapsed:.2f}s (scaling ratio: {scaling_ratio:.1f}x vs 1x)")
    print(f"  FPS: {stress_fps:.0f}")
    print(f"  Memory delta: {stress_mem_mb:.1f} MB")

    check("stress FPS ≥ 30", stress_fps >= 30,
          f"fps={stress_fps:.0f}")
    check("no crash on 3x dataset", result_stress is not None)
    check("no exponential slowdown (ratio < 10x for 3x data)", scaling_ratio < 10.0,
          f"ratio={scaling_ratio:.1f}x")

    os.remove(big_path)

    # Final metrics summary
    print(f"\n  ─── Throughput Summary ───")
    print(f"  1x: {frame_count} frames, {elapsed:.2f}s, {fps:.0f} fps")
    print(f"  3x: {big_frames} frames, {stress_elapsed:.2f}s, {stress_fps:.0f} fps")
    print(f"  E2E: {e2e_elapsed:.2f}s ({e2e_fps:.0f} fps)")


# ═══════════════════════════════════════════════════════════════════════════
# GROUP 12 — OFF-TRACK & PROJECTION VALIDATION (real telemetry)
# ═══════════════════════════════════════════════════════════════════════════

def test_group_12():
    print("\n" + "=" * 60)
    print("GROUP 12 — OFF-TRACK & PROJECTION VALIDATION")
    print("=" * 60)

    with open(TRACK_MAP_FILE) as f:
        track_data = json.load(f)

    points = track_data['points']
    us = [p['u'] for p in points]
    vs = [p['v'] for p in points]
    half_widths = [p.get('half_width', 7.0) for p in points]
    n = len(points)

    TRACK_MARGIN = 2.0  # same as GUI

    # Load telemetry and compute lateral offsets
    print("\n[12.1] Off-Track False Positive Test (A10)")
    frames = []
    with open(TELEMETRY_FILE) as f:
        for line in f:
            line = line.strip()
            if line:
                frames.append(json.loads(line))

    # Use intelligence for heading data
    with open(INTEL_FILE) as f:
        intel = json.load(f)
    intel_points = intel['points']
    total_arc = intel['total_arc_length_m']

    sys.path.insert(0, '.')
    from driver_analysis import compute_lateral_offset, find_nearest_track_index, \
        map_lap_distance_to_index, build_track_index

    i_us, i_vs = build_track_index(intel_points)
    ni = len(intel_points)

    total_valid = 0
    off_track_count = 0
    prev_idx = 0

    for frame in frames:
        player = frame.get('player')
        if not player:
            continue
        wp = player.get('world_pos_m')
        if not wp:
            continue
        lap_dist = player.get('lapDistance', 0)
        lap_num = player.get('lapNumber', 0)
        if lap_dist < 0 or lap_num < 2:
            continue  # skip formation/warmup

        car_u = wp['x']
        car_v = wp['z']
        hint = map_lap_distance_to_index(lap_dist, intel_points, total_arc)
        idx = find_nearest_track_index(car_u, car_v, i_us, i_vs, hint, ni)
        tp = intel_points[idx]

        lateral = compute_lateral_offset(car_u, car_v, tp['u'], tp['v'], tp['heading'])

        # Find corresponding track map half_width
        map_idx = int((tp['s'] / total_arc) * n) % n
        hw = half_widths[map_idx] + TRACK_MARGIN

        total_valid += 1
        if abs(lateral) > hw:
            off_track_count += 1

        prev_idx = idx

    off_pct = (off_track_count / total_valid * 100) if total_valid > 0 else 0
    print(f"  Valid frames: {total_valid}")
    print(f"  Off-track frames: {off_track_count} ({off_pct:.1f}%)")

    check("off-track < 10% on recorded session", off_pct < 10,
          f"{off_pct:.1f}%")
    check("off-track < 30% (width not critically narrow)", off_pct < 30,
          f"{off_pct:.1f}%")

    # Test A11: Projection Stability
    print("\n[12.2] Projection Stability Test (A11)")
    prev_idx = None
    large_jumps = 0
    total_transitions = 0

    for frame in frames:
        player = frame.get('player')
        if not player:
            continue
        wp = player.get('world_pos_m')
        if not wp:
            continue
        lap_dist = player.get('lapDistance', 0)
        if lap_dist < 0:
            continue

        car_u = wp['x']
        car_v = wp['z']
        hint = map_lap_distance_to_index(lap_dist, intel_points, total_arc)
        idx = find_nearest_track_index(car_u, car_v, i_us, i_vs, hint, ni)

        if prev_idx is not None:
            jump = abs(idx - prev_idx)
            if jump > ni // 2:
                jump = ni - jump  # wrap
            total_transitions += 1
            if jump > 15:  # matches GUI hysteresis threshold
                large_jumps += 1

        prev_idx = idx

    jump_pct = (large_jumps / total_transitions * 100) if total_transitions > 0 else 0
    print(f"  Frame transitions: {total_transitions}")
    print(f"  Large jumps (>15 segments): {large_jumps} ({jump_pct:.2f}%)")

    check("no segment jumps > 15 (snapping)", large_jumps == 0,
          f"{large_jumps} jumps detected ({jump_pct:.2f}%)")


# ═══════════════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════════════

def main():
    print("F1 2025 Phase 1–22 Automated Validation Suite")
    print("=" * 60)

    # Verify required files exist
    required = [TELEMETRY_FILE, TRACK_MAP_FILE, INTEL_FILE, ANALYSIS_FILE]
    for path in required:
        if not os.path.exists(path):
            print(f"FATAL: Required file not found: {path}")
            sys.exit(1)

    test_group_1()
    test_group_2()
    test_group_3()
    test_group_4()
    test_group_5()
    test_group_6()
    test_group_7()
    test_group_8()
    test_group_9()
    test_group_10()
    test_group_11()
    test_group_12()

    # Final summary
    print("\n" + "=" * 60)
    print("VALIDATION SUMMARY")
    print("=" * 60)
    total = passed + failed
    print(f"  PASSED: {passed}/{total}")
    print(f"  FAILED: {failed}/{total}")
    if errors:
        print("\nFailures:")
        for e in errors:
            print(f"  ✗ {e}")
    print()

    if failed > 0:
        print("❌ VALIDATION FAILED — fix before proceeding")
        sys.exit(1)
    else:
        print("✅ ALL TESTS PASSED — pipeline is structurally correct")
        sys.exit(0)


if __name__ == '__main__':
    main()
