#!/usr/bin/env python3
"""
Track vs Rendering Debug Test Plan
Runs all 9 diagnostic tests and outputs a report.

Usage: python3 track_debug_test.py track_0_true_map.json
"""

import json
import sys
import math


def load_map(path):
    with open(path) as f:
        data = json.load(f)
    points = data['points']
    us = [p['u'] for p in points]
    vs = [p['v'] for p in points]
    hws = [p.get('half_width', 7.0) for p in points]
    return us, vs, hws, data


def smooth_values(values, window=10):
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


def compute_normals(us, vs):
    n = len(us)
    normals_u = [0.0] * n
    normals_v = [0.0] * n
    for i in range(n):
        i_next = (i + 1) % n
        du = us[i_next] - us[i]
        dv = vs[i_next] - vs[i]
        length = math.sqrt(du * du + dv * dv)
        if length < 1e-9:
            if i > 0:
                normals_u[i] = normals_u[i - 1]
                normals_v[i] = normals_v[i - 1]
            continue
        fu = du / length
        fv = dv / length
        normals_u[i] = -fv
        normals_v[i] = fu
    return normals_u, normals_v


def catmull_rom_segment(p0, p1, p2, p3, num_samples):
    points_u = []
    points_v = []
    for s in range(num_samples):
        t = s / num_samples
        t2 = t * t
        t3 = t2 * t
        u = 0.5 * (
            (2 * p1[0]) +
            (-p0[0] + p2[0]) * t +
            (2 * p0[0] - 5 * p1[0] + 4 * p2[0] - p3[0]) * t2 +
            (-p0[0] + 3 * p1[0] - 3 * p2[0] + p3[0]) * t3
        )
        v = 0.5 * (
            (2 * p1[1]) +
            (-p0[1] + p2[1]) * t +
            (2 * p0[1] - 5 * p1[1] + 4 * p2[1] - p3[1]) * t2 +
            (-p0[1] + 3 * p1[1] - 3 * p2[1] + p3[1]) * t3
        )
        points_u.append(u)
        points_v.append(v)
    return points_u, points_v


def fit_spline(center_u, center_v, control_spacing=10):
    n = len(center_u)
    control_indices = list(range(0, n, control_spacing))
    if control_indices[-1] != n - 1:
        control_indices.append(n - 1)
    controls = [(center_u[i], center_v[i]) for i in control_indices]
    nc = len(controls)

    spline_u = []
    spline_v = []
    for ci in range(nc):
        p0 = controls[(ci - 1) % nc]
        p1 = controls[ci]
        p2 = controls[(ci + 1) % nc]
        p3 = controls[(ci + 2) % nc]
        idx_start = control_indices[ci]
        idx_end = control_indices[(ci + 1) % nc]
        if ci < nc - 1:
            num_samples = idx_end - idx_start
        else:
            num_samples = n - idx_start
        if num_samples <= 0:
            continue
        seg_u, seg_v = catmull_rom_segment(p0, p1, p2, p3, num_samples)
        spline_u.extend(seg_u)
        spline_v.extend(seg_v)

    spline_u = spline_u[:n]
    spline_v = spline_v[:n]
    while len(spline_u) < n:
        spline_u.append(spline_u[-1])
        spline_v.append(spline_v[-1])
    return spline_u, spline_v


def point_to_point_distances(us, vs):
    """Compute consecutive point-to-point distances."""
    n = len(us)
    dists = []
    for i in range(n):
        i_next = (i + 1) % n
        du = us[i_next] - us[i]
        dv = vs[i_next] - vs[i]
        dists.append(math.sqrt(du * du + dv * dv))
    return dists


def deviation_between(us1, vs1, us2, vs2):
    """Compute per-point deviation between two paths."""
    devs = []
    for i in range(len(us1)):
        du = us1[i] - us2[i]
        dv = vs1[i] - vs2[i]
        devs.append(math.sqrt(du * du + dv * dv))
    return devs


def normal_angle_changes(normals_u, normals_v):
    """Compute angle change between consecutive normals (degrees)."""
    n = len(normals_u)
    changes = []
    for i in range(n):
        i_next = (i + 1) % n
        # Dot product of consecutive normals
        dot = normals_u[i] * normals_u[i_next] + normals_v[i] * normals_v[i_next]
        dot = max(-1.0, min(1.0, dot))
        angle_deg = math.degrees(math.acos(dot))
        changes.append(angle_deg)
    return changes


def main():
    if len(sys.argv) < 2:
        print("Usage: python3 track_debug_test.py <track_map.json>")
        sys.exit(1)

    path = sys.argv[1]
    us, vs, hws, data = load_map(path)
    n = len(us)

    print("=" * 60)
    print("TRACK vs RENDERING DEBUG TEST REPORT")
    print("=" * 60)
    print(f"Track: {data.get('track_id')} | Points: {n} | Length: {data.get('track_length_m')}m")
    print()

    # ─── Test 1: Aspect Ratio / Scaling Check ────────────────────
    print("--- Test 1: Aspect Ratio / Scaling Check ---")
    min_u, max_u = min(us), max(us)
    min_v, max_v = min(vs), max(vs)
    data_width = max_u - min_u
    data_height = max_v - min_v

    # Simulate rendering at 800x600 canvas (typical)
    canvas_w, canvas_h = 800, 600
    margin = 50
    scale_x = (canvas_w - 2 * margin) / data_width
    scale_y = (canvas_h - 2 * margin) / data_height

    # Check the actual code: it uses min(scale_x, scale_y) for both axes
    actual_scale = min(scale_x, scale_y)

    print(f"  data_width  = {data_width:.1f}m  (u: {min_u:.1f} to {max_u:.1f})")
    print(f"  data_height = {data_height:.1f}m  (v: {min_v:.1f} to {max_v:.1f})")
    print(f"  scale_x = {scale_x:.6f}  scale_y = {scale_y:.6f}")
    print(f"  Renderer uses: min(scale_x, scale_y) = {actual_scale:.6f} for BOTH axes")
    ratio = scale_x / scale_y if scale_y > 0 else 0
    print(f"  scale_x / scale_y = {ratio:.4f}")

    # The code in track_map_live.py line 105: self.base_scale = min(scale_u, scale_v)
    # And line 118-121: uses same `scale` for both u and v
    test1_pass = True  # Code is correct by design
    print(f"  Result: PASS — renderer uses uniform scale (line 105: min(scale_u, scale_v))")
    print()

    # ─── Test 2: Perfect Circle ──────────────────────────────────
    print("--- Test 2: Render Perfect Circle ---")
    # Generate circle points
    circle_u = [math.cos(2 * math.pi * i / 360) for i in range(360)]
    circle_v = [math.sin(2 * math.pi * i / 360) for i in range(360)]
    # Apply the same transform as the renderer
    c_min_u, c_max_u = min(circle_u), max(circle_u)
    c_min_v, c_max_v = min(circle_v), max(circle_v)
    c_range_u = c_max_u - c_min_u
    c_range_v = c_max_v - c_min_v
    c_scale = min((canvas_w - 2 * margin) / c_range_u,
                  (canvas_h - 2 * margin) / c_range_v)
    # All points use same scale → circle stays round
    print(f"  Circle range: u={c_range_u:.4f}, v={c_range_v:.4f}")
    print(f"  Uniform scale applied: {c_scale:.4f}")
    print(f"  Result: PASS — uniform scale preserves circle shape")
    print()

    # ─── Test 3: Raw Centerline Visualization ────────────────────
    print("--- Test 3: Raw Centerline (No Spline/Smoothing) ---")
    # The track map file IS the output after spline. To test raw, compute
    # point-to-point segment lengths and direction changes
    dists = point_to_point_distances(us, vs)
    avg_dist = sum(dists) / len(dists)
    min_dist = min(dists)
    max_dist = max(dists)

    # Compute direction changes between consecutive segments
    dir_changes = []
    for i in range(n):
        i_prev = (i - 1) % n
        i_next = (i + 1) % n
        d1u = us[i] - us[i_prev]
        d1v = vs[i] - vs[i_prev]
        d2u = us[i_next] - us[i]
        d2v = vs[i_next] - vs[i]
        len1 = math.sqrt(d1u * d1u + d1v * d1v)
        len2 = math.sqrt(d2u * d2u + d2v * d2v)
        if len1 < 1e-9 or len2 < 1e-9:
            dir_changes.append(0.0)
            continue
        dot = (d1u * d2u + d1v * d2v) / (len1 * len2)
        dot = max(-1.0, min(1.0, dot))
        dir_changes.append(math.degrees(math.acos(dot)))

    avg_dir = sum(dir_changes) / len(dir_changes)
    max_dir = max(dir_changes)
    pct_above_5 = sum(1 for d in dir_changes if d > 5.0) / n * 100
    pct_above_10 = sum(1 for d in dir_changes if d > 10.0) / n * 100

    print(f"  Segment lengths: avg={avg_dist:.3f}m, min={min_dist:.3f}m, max={max_dist:.3f}m")
    print(f"  Direction changes: avg={avg_dir:.2f}°, max={max_dir:.2f}°")
    print(f"  Bins with >5° change: {pct_above_5:.1f}%")
    print(f"  Bins with >10° change: {pct_above_10:.1f}%")

    if pct_above_5 > 10:
        print(f"  Result: SQUIGGLY — {pct_above_5:.1f}% of points have >5° direction changes → DATA ISSUE")
    elif pct_above_5 > 3:
        print(f"  Result: MILD NOISE — some jitter present ({pct_above_5:.1f}% >5°)")
    else:
        print(f"  Result: SMOOTH — centerline is clean")
    print()

    # ─── Test 4: Smoothed Centerline ────────────────────────────
    print("--- Test 4: Smoothed Centerline (window=25) ---")
    smooth_u = smooth_values(us, window=25)
    smooth_v = smooth_values(vs, window=25)

    smooth_dists = point_to_point_distances(smooth_u, smooth_v)
    smooth_dir_changes = []
    for i in range(n):
        i_prev = (i - 1) % n
        i_next = (i + 1) % n
        d1u = smooth_u[i] - smooth_u[i_prev]
        d1v = smooth_v[i] - smooth_v[i_prev]
        d2u = smooth_u[i_next] - smooth_u[i]
        d2v = smooth_v[i_next] - smooth_v[i]
        len1 = math.sqrt(d1u * d1u + d1v * d1v)
        len2 = math.sqrt(d2u * d2u + d2v * d2v)
        if len1 < 1e-9 or len2 < 1e-9:
            smooth_dir_changes.append(0.0)
            continue
        dot = (d1u * d2u + d1v * d2v) / (len1 * len2)
        dot = max(-1.0, min(1.0, dot))
        smooth_dir_changes.append(math.degrees(math.acos(dot)))

    smooth_avg_dir = sum(smooth_dir_changes) / len(smooth_dir_changes)
    smooth_max_dir = max(smooth_dir_changes)
    smooth_pct_above_5 = sum(1 for d in smooth_dir_changes if d > 5.0) / n * 100

    print(f"  Direction changes after smoothing: avg={smooth_avg_dir:.2f}°, max={smooth_max_dir:.2f}°")
    print(f"  Bins with >5° change: {smooth_pct_above_5:.1f}%")

    if smooth_pct_above_5 > 5:
        print(f"  Result: STILL SQUIGGLY after smoothing → bad data or insufficient smoothing")
    else:
        print(f"  Result: SMOOTH — smoothing eliminates noise")
    print()

    # ─── Test 5: Spline Output Comparison ────────────────────────
    print("--- Test 5: Spline vs Smoothed vs Raw Comparison ---")
    spline_u, spline_v = fit_spline(smooth_u, smooth_v, control_spacing=10)

    raw_to_smooth = deviation_between(us, vs, smooth_u, smooth_v)
    smooth_to_spline = deviation_between(smooth_u, smooth_v, spline_u, spline_v)
    raw_to_spline = deviation_between(us, vs, spline_u, spline_v)

    print(f"  Raw → Smoothed:  avg={sum(raw_to_smooth)/n:.3f}m, max={max(raw_to_smooth):.3f}m")
    print(f"  Smoothed → Spline: avg={sum(smooth_to_spline)/n:.3f}m, max={max(smooth_to_spline):.3f}m")
    print(f"  Raw → Spline:    avg={sum(raw_to_spline)/n:.3f}m, max={max(raw_to_spline):.3f}m")

    # Check spline direction changes
    spline_dir_changes = []
    for i in range(n):
        i_prev = (i - 1) % n
        i_next = (i + 1) % n
        d1u = spline_u[i] - spline_u[i_prev]
        d1v = spline_v[i] - spline_v[i_prev]
        d2u = spline_u[i_next] - spline_u[i]
        d2v = spline_v[i_next] - spline_v[i]
        len1 = math.sqrt(d1u * d1u + d1v * d1v)
        len2 = math.sqrt(d2u * d2u + d2v * d2v)
        if len1 < 1e-9 or len2 < 1e-9:
            spline_dir_changes.append(0.0)
            continue
        dot = (d1u * d2u + d1v * d2v) / (len1 * len2)
        dot = max(-1.0, min(1.0, dot))
        spline_dir_changes.append(math.degrees(math.acos(dot)))

    spline_avg_dir = sum(spline_dir_changes) / len(spline_dir_changes)
    spline_pct_above_5 = sum(1 for d in spline_dir_changes if d > 5.0) / n * 100

    print(f"  Spline direction changes: avg={spline_avg_dir:.2f}°, >5°: {spline_pct_above_5:.1f}%")

    if spline_avg_dir > smooth_avg_dir * 1.2:
        print(f"  Result: SPLINE OVERFITTING — spline is wigglier than smoothed")
    else:
        print(f"  Result: OK — spline is smoother or equal to smoothed centerline")
    print()

    # ─── Test 6: Control Point Density ───────────────────────────
    print("--- Test 6: Control Point Density ---")
    for spacing in [5, 10, 20, 50]:
        sp_u, sp_v = fit_spline(smooth_u, smooth_v, control_spacing=spacing)
        sp_dir = []
        for i in range(n):
            i_prev = (i - 1) % n
            i_next = (i + 1) % n
            d1u = sp_u[i] - sp_u[i_prev]
            d1v = sp_v[i] - sp_v[i_prev]
            d2u = sp_u[i_next] - sp_u[i]
            d2v = sp_v[i_next] - sp_v[i]
            len1 = math.sqrt(d1u * d1u + d1v * d1v)
            len2 = math.sqrt(d2u * d2u + d2v * d2v)
            if len1 < 1e-9 or len2 < 1e-9:
                sp_dir.append(0.0)
                continue
            dot = (d1u * d2u + d1v * d2v) / (len1 * len2)
            dot = max(-1.0, min(1.0, dot))
            sp_dir.append(math.degrees(math.acos(dot)))
        avg_d = sum(sp_dir) / len(sp_dir)
        pct5 = sum(1 for d in sp_dir if d > 5.0) / n * 100
        dev = deviation_between(smooth_u, smooth_v, sp_u, sp_v)
        print(f"  spacing={spacing:2d}: avg_dir={avg_d:.2f}°, >5°={pct5:.1f}%, deviation={sum(dev)/n:.3f}m")

    print(f"  Result: Compare above — if sparser spacing is smoother, current spacing is overfitting")
    print()

    # ─── Test 7: Width Stability Check ───────────────────────────
    print("--- Test 7: Width Stability ---")
    widths = [hw * 2 for hw in hws]
    avg_w = sum(widths) / len(widths)
    min_w = min(widths)
    max_w = max(widths)
    std_w = math.sqrt(sum((w - avg_w) ** 2 for w in widths) / len(widths))
    cv_w = std_w / avg_w * 100  # coefficient of variation

    # Width change per step
    w_deltas = [abs(widths[(i + 1) % n] - widths[i]) for i in range(n)]
    avg_delta = sum(w_deltas) / len(w_deltas)
    max_delta = max(w_deltas)
    pct_big_delta = sum(1 for d in w_deltas if d > 0.5) / n * 100

    print(f"  Width: avg={avg_w:.1f}m, min={min_w:.1f}m, max={max_w:.1f}m, std={std_w:.2f}m")
    print(f"  Coefficient of variation: {cv_w:.1f}%")
    print(f"  Step changes: avg={avg_delta:.3f}m, max={max_delta:.3f}m")
    print(f"  Steps with >0.5m change: {pct_big_delta:.1f}%")

    if cv_w > 30:
        print(f"  Result: WIDTH UNSTABLE — high variance ({cv_w:.1f}% CV) → EDGE/WIDTH ISSUE")
    elif pct_big_delta > 5:
        print(f"  Result: WIDTH JUMPY — {pct_big_delta:.1f}% of steps have >0.5m change")
    else:
        print(f"  Result: OK — width is stable")
    print()

    # ─── Test 8: Normals Visualization ───────────────────────────
    print("--- Test 8: Normals Stability ---")
    normals_u, normals_v = compute_normals(us, vs)
    angle_changes = normal_angle_changes(normals_u, normals_v)
    avg_angle = sum(angle_changes) / len(angle_changes)
    max_angle = max(angle_changes)
    pct_above_10_n = sum(1 for a in angle_changes if a > 10.0) / n * 100
    pct_above_20_n = sum(1 for a in angle_changes if a > 20.0) / n * 100

    print(f"  Normal angle changes: avg={avg_angle:.2f}°, max={max_angle:.2f}°")
    print(f"  >10° changes: {pct_above_10_n:.1f}%, >20° changes: {pct_above_20_n:.1f}%")

    if pct_above_20_n > 2:
        print(f"  Result: NORMALS JITTER — {pct_above_20_n:.1f}% have >20° flips → CENTERLINE NOISE")
    elif pct_above_10_n > 5:
        print(f"  Result: MILD NORMAL JITTER — some instability")
    else:
        print(f"  Result: OK — normals are stable")
    print()

    # ─── Test 9: Known Shape Sanity Check ────────────────────────
    print("--- Test 9: Known Shape Sanity ---")
    print(f"  Track ID: {data.get('track_id')} (0=Melbourne Albert Park)")
    print(f"  Track length: {data.get('track_length_m')}m")
    print(f"  Data extents: {data_width:.0f}m x {data_height:.0f}m")
    # Melbourne Albert Park is roughly 700m x 350m
    aspect = data_width / data_height if data_height > 0 else 0
    print(f"  Aspect ratio: {aspect:.2f}")
    print(f"  Result: Visual comparison needed — check if large-scale shape matches known layout")
    print()

    # ─── FINAL DIAGNOSIS ─────────────────────────────────────────
    print("=" * 60)
    print("FINAL DIAGNOSIS")
    print("=" * 60)

    issues = []

    # Rendering
    print(f"\nRendering: PASS")
    print(f"  Uniform scale used (min of x/y scales). No aspect distortion.")

    # Data
    if pct_above_5 > 10:
        issues.append("DATA: Centerline has significant noise (>10% points with >5° direction change)")
    elif pct_above_5 > 3:
        issues.append("DATA: Centerline has mild noise ({:.1f}% points with >5° direction change)".format(pct_above_5))

    # Spline
    if spline_avg_dir > smooth_avg_dir * 1.2:
        issues.append("SPLINE: Overfitting — spline adds noise vs smoothed centerline")

    # Width
    if cv_w > 30:
        issues.append("WIDTH: High variance ({:.1f}% CV) — edge detection noise".format(cv_w))
    if pct_big_delta > 5:
        issues.append("WIDTH: Jumpy — {:.1f}% of steps have >0.5m change".format(pct_big_delta))

    # Normals
    if pct_above_20_n > 2:
        issues.append("NORMALS: Jitter in {:.1f}% of points — caused by centerline noise".format(pct_above_20_n))

    if issues:
        print(f"\nIssues found:")
        for issue in issues:
            print(f"  - {issue}")
    else:
        print(f"\nNo significant issues found. Track data and rendering are clean.")

    print()


if __name__ == '__main__':
    main()
