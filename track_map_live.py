#!/usr/bin/env python3
"""
F1 2025 Live Track Map GUI

Displays a real-time track map with the player car's position.
Reads a pre-built track map JSON and live telemetry from stdin,
or replays a recorded JSONL file.

Controls:
    Scroll wheel    Zoom in/out
    Click + drag    Pan the map
    R               Reset zoom to fit
    F               Follow player car (toggle)
    +/-             Zoom in/out

Replay controls:
    Space           Play / pause
    Left / Right    Skip -5s / +5s
    1 / 2 / 3 / 4  Speed 1x / 2x / 4x / 0.5x
    Click bar       Seek to position

Usage:
    mvn -q exec:java ... 2>&1 | python3 track_map_live.py <track_map.json>
    python3 track_map_live.py <track_map.json> --replay <telemetry.jsonl>
"""

import json
import sys
import os
import math
import time
import threading
import tkinter as tk


# ─── Track Map Loading ────────────────────────────────────────────────────────

def load_track_map(path):
    """Load track map JSON file and precompute normal vectors."""
    with open(path) as f:
        data = json.load(f)
    points = data['points']
    us = [p['u'] for p in points]
    vs = [p['v'] for p in points]

    # Per-point half_width (from true centerline maps), fallback to constant
    half_widths = [p.get('half_width', TRACK_HALF_WIDTH_M) for p in points]

    # Use spline-derived normals if available (from builder), otherwise compute
    has_spline_normals = data.get('spline_normals', False) and 'nu' in points[0]
    n = len(us)

    if has_spline_normals:
        normals_u = [p['nu'] for p in points]
        normals_v = [p['nv'] for p in points]
    else:
        # Fallback: compute normals from centerline points
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

    is_true = data.get('true_centerline', False)
    if is_true:
        src = "spline-derived" if has_spline_normals else "computed"
        print(f"[track_map] True centerline map loaded (per-point width, {src} normals)")

    # Auto-load corner data from intelligence file if available
    corners = []
    track_id = data.get('track_id')
    if track_id is not None:
        intel_path = os.path.join(os.path.dirname(path), f"track_{track_id}_intelligence.json")
        if os.path.exists(intel_path):
            try:
                with open(intel_path) as f:
                    intel = json.load(f)
                # Find apex midpoint for each corner
                corner_apexes = {}
                for p in intel['points']:
                    cid = p.get('corner_id', -1)
                    if cid >= 0 and p.get('corner_phase') == 'apex':
                        if cid not in corner_apexes:
                            corner_apexes[cid] = []
                        corner_apexes[cid].append(p)
                for cid in sorted(corner_apexes.keys()):
                    pts = corner_apexes[cid]
                    mid = pts[len(pts) // 2]
                    heading = mid.get('heading', 0)
                    # Normal perpendicular to heading
                    nu_val = -math.sin(heading)
                    nv_val = math.cos(heading)
                    # Find nearest track map point for half_width
                    # Use simple distance search
                    best_hw = 5.0
                    best_dist = float('inf')
                    for k in range(0, n, max(1, n // 200)):
                        du = us[k] - mid['u']
                        dv = vs[k] - mid['v']
                        d2 = du * du + dv * dv
                        if d2 < best_dist:
                            best_dist = d2
                            best_hw = half_widths[k]
                    # Place label outside the track edge
                    label_offset = best_hw + 8.0  # meters beyond centerline
                    # Curvature sign determines which side is "outside"
                    curv = mid.get('curvature', 0)
                    sign = 1.0 if curv >= 0 else -1.0
                    corners.append({
                        'id': cid,
                        'u': mid['u'] + sign * nu_val * label_offset,
                        'v': mid['v'] + sign * nv_val * label_offset,
                    })
                print(f"[track_map] Loaded {len(corners)} corner labels from intelligence")
            except (json.JSONDecodeError, KeyError) as e:
                print(f"[track_map] Warning: could not load corners from {intel_path}: {e}")

    return {
        'track_id': track_id,
        'track_length': data.get('track_length_m', len(points)),
        'u_axis': data.get('coordinate_axes', {}).get('u', 'u'),
        'v_axis': data.get('coordinate_axes', {}).get('v', 'v'),
        'us': us,
        'vs': vs,
        'normals_u': normals_u,
        'normals_v': normals_v,
        'half_widths': half_widths,
        'true_centerline': is_true,
        'num_points': len(points),
        'corners': corners,
    }


# ─── Coordinate Transform with Zoom/Pan ──────────────────────────────────────

class CoordTransform:
    """Maps track (u, v) coordinates to canvas pixel coordinates with zoom/pan."""

    def __init__(self, us, vs, canvas_w, canvas_h, margin=50):
        self.canvas_w = canvas_w
        self.canvas_h = canvas_h

        self.min_u, self.max_u = min(us), max(us)
        self.min_v, self.max_v = min(vs), max(vs)

        range_u = self.max_u - self.min_u or 1.0
        range_v = self.max_v - self.min_v or 1.0

        scale_u = (canvas_w - 2 * margin) / range_u
        scale_v = (canvas_h - 2 * margin) / range_v
        self.base_scale = min(scale_u, scale_v)

        # Center of track in track coords
        self.center_u = (self.min_u + self.max_u) / 2.0
        self.center_v = (self.min_v + self.max_v) / 2.0

        # Zoom and pan state
        self.zoom = 1.0
        self.pan_x = 0.0  # pixel offset
        self.pan_y = 0.0

    def to_canvas(self, u, v):
        """Convert track (u, v) to canvas (x, y)."""
        scale = self.base_scale * self.zoom
        cx = (u - self.center_u) * scale + self.canvas_w / 2.0 + self.pan_x
        cy = (v - self.center_v) * scale + self.canvas_h / 2.0 + self.pan_y
        return cx, cy

    def to_track(self, cx, cy):
        """Convert canvas (x, y) back to track (u, v)."""
        scale = self.base_scale * self.zoom
        u = (cx - self.canvas_w / 2.0 - self.pan_x) / scale + self.center_u
        v = (cy - self.canvas_h / 2.0 - self.pan_y) / scale + self.center_v
        return u, v

    def zoom_at(self, factor, cx, cy):
        """Zoom by factor, keeping canvas point (cx, cy) fixed."""
        # Track coord under cursor before zoom
        tu, tv = self.to_track(cx, cy)

        self.zoom *= factor

        # Where that track coord maps after zoom
        new_cx, new_cy = self.to_canvas(tu, tv)

        # Adjust pan so the cursor stays over the same track point
        self.pan_x += cx - new_cx
        self.pan_y += cy - new_cy

    def reset(self, canvas_w, canvas_h):
        """Reset to fit the full track."""
        self.canvas_w = canvas_w
        self.canvas_h = canvas_h
        self.zoom = 1.0
        self.pan_x = 0.0
        self.pan_y = 0.0

    def center_on(self, u, v):
        """Center the view on a track coordinate."""
        scale = self.base_scale * self.zoom
        target_cx = self.canvas_w / 2.0
        target_cy = self.canvas_h / 2.0
        current_cx = (u - self.center_u) * scale + self.canvas_w / 2.0 + self.pan_x
        current_cy = (v - self.center_v) * scale + self.canvas_h / 2.0 + self.pan_y
        self.pan_x += target_cx - current_cx
        self.pan_y += target_cy - current_cy


# ─── Car Position Lookup ─────────────────────────────────────────────────────

def lookup_position(track_map, lap_distance):
    """Look up (u, v) on track map from lap distance with interpolation."""
    n = track_map['num_points']
    if n == 0:
        return 0, 0

    s = lap_distance % track_map['track_length']
    if s < 0:
        s += track_map['track_length']

    i = int(s)
    if i >= n - 1:
        return track_map['us'][-1], track_map['vs'][-1]

    t = s - i
    u = track_map['us'][i] + t * (track_map['us'][i + 1] - track_map['us'][i])
    v = track_map['vs'][i] + t * (track_map['vs'][i + 1] - track_map['vs'][i])
    return u, v


TRACK_HALF_WIDTH_M = 7.0  # F1 track is ~14m wide


def lookup_normal(track_map, lap_distance):
    """Look up interpolated normal vector (nu, nv) at lap distance."""
    n = track_map['num_points']
    if n == 0:
        return 1.0, 0.0

    s = lap_distance % track_map['track_length']
    if s < 0:
        s += track_map['track_length']

    i = int(s)
    if i >= n - 1:
        return track_map['normals_u'][-1], track_map['normals_v'][-1]

    t = s - i
    nu = track_map['normals_u'][i] + t * (track_map['normals_u'][i + 1] - track_map['normals_u'][i])
    nv = track_map['normals_v'][i] + t * (track_map['normals_v'][i + 1] - track_map['normals_v'][i])

    # Re-normalize
    length = math.sqrt(nu * nu + nv * nv)
    if length > 1e-9:
        nu /= length
        nv /= length
    return nu, nv


def project_world_to_2d(track_map, world_pos):
    """Project 3D world position to 2D track coords using coordinate_axes mapping."""
    if not world_pos:
        return None
    u_axis = track_map.get('u_axis', 'x')
    v_axis = track_map.get('v_axis', 'z')
    u = world_pos.get(u_axis, 0.0)
    v = world_pos.get(v_axis, 0.0)
    if u == 0.0 and v == 0.0:
        return None
    return u, v


# Projection state machine phases
_ST_INIT = 0        # not yet initialized — needs global search
_ST_TRACKING = 1    # normal: ±5 strict
_ST_UNSTABLE = 2    # relaxed: ±15, looser thresholds
_ST_RECOVERING = 3  # global reset


class CarProjectionState:
    """Per-car projection tracking with state machine."""
    __slots__ = ('phase', 'prev_seg_idx', 'prev_u', 'prev_v',
                 'prev_world_u', 'prev_world_v', 'invalid_count',
                 'prev_lateral', 'off_track_count',
                 'vel_u', 'vel_v', 'last_seen')

    def __init__(self):
        self.phase = _ST_INIT
        self.prev_seg_idx = None
        self.prev_u = None
        self.prev_v = None
        self.prev_world_u = None
        self.prev_world_v = None
        self.invalid_count = 0
        self.prev_lateral = 0.0
        self.off_track_count = 0
        self.vel_u = 0.0
        self.vel_v = 0.0
        self.last_seen = 0.0  # timestamp of last update

    def invalidate(self):
        """Force reinitialization."""
        self.phase = _ST_INIT
        self.prev_seg_idx = None
        self.invalid_count = 0


# Per-car state: keyed by car identifier ('player' or car index)
_car_states = {}


def _get_car_state(car_id):
    if car_id not in _car_states:
        _car_states[car_id] = CarProjectionState()
    return _car_states[car_id]


CONTINUITY_LAMBDA = 0.3  # soft penalty per index difference


def _find_best_segment(car_u, car_v, us, vs, n, center_idx, search_radius,
                       prev_idx=None, vel_u=0, vel_v=0):
    """Search for best segment with direction-aware + continuity scoring.

    score = distance + 0.3 * index_penalty + 0.3 * angle_penalty
    Rejects segments going opposite to car velocity (dot < -0.2).

    Returns (seg_idx, proj_u, proj_v, dist_sq, t_param).
    """
    has_vel = (vel_u * vel_u + vel_v * vel_v) > 0.01

    best_score = float('inf')
    best_dist_sq = float('inf')
    best_proj_u = us[center_idx]
    best_proj_v = vs[center_idx]
    best_seg_idx = center_idx
    best_t = 0.0

    for offset in range(-search_radius, search_radius + 1):
        i = (center_idx + offset) % n
        i_next = (i + 1) % n

        seg_du = us[i_next] - us[i]
        seg_dv = vs[i_next] - vs[i]
        seg_len_sq = seg_du * seg_du + seg_dv * seg_dv

        if seg_len_sq < 1e-12:
            continue

        # Direction filter: reject segments going opposite to velocity
        if has_vel:
            seg_len = math.sqrt(seg_len_sq)
            dot_dir = (seg_du * vel_u + seg_dv * vel_v) / seg_len
            if dot_dir < -0.2:
                continue  # opposite direction

        wu = car_u - us[i]
        wv = car_v - vs[i]
        t = (wu * seg_du + wv * seg_dv) / seg_len_sq
        t = max(0.0, min(1.0, t))

        proj_u = us[i] + seg_du * t
        proj_v = vs[i] + seg_dv * t

        du = car_u - proj_u
        dv = car_v - proj_v
        dist_sq = du * du + dv * dv

        # Combined scoring: distance + continuity + direction
        score = dist_sq

        if prev_idx is not None:
            idx_delta = abs(i - prev_idx)
            if idx_delta > n // 2:
                idx_delta = n - idx_delta
            score += CONTINUITY_LAMBDA * idx_delta

        if has_vel:
            seg_len = math.sqrt(seg_len_sq)
            dot_dir = (seg_du * vel_u + seg_dv * vel_v) / seg_len
            angle_penalty = 1.0 - max(0.0, dot_dir)
            score += 0.3 * angle_penalty

        if score < best_score:
            best_score = score
            best_dist_sq = dist_sq
            best_proj_u = proj_u
            best_proj_v = proj_v
            best_seg_idx = i
            best_t = t

    return best_seg_idx, best_proj_u, best_proj_v, best_dist_sq, best_t


STRICT_DIST_SQ = 10.0 * 10.0   # 10m — TRACKING
RELAXED_DIST_SQ = 15.0 * 15.0  # 15m — UNSTABLE


_in_render_loop = False  # runtime guard: projection must not be called during render


def compute_track_position(track_map, world_pos, lap_distance, car_id='player',
                           speed_kmh=0, dt=1/30, player_seg_idx=None):
    """Compute car's 2D position using state-machine projection.

    States: INIT → TRACKING ↔ UNSTABLE → RECOVERING → TRACKING
    Never freezes: escalates automatically when stuck.

    Returns (u, v, lateral_offset, is_off_track).
    """
    if _in_render_loop:
        raise RuntimeError("Projection called during render loop — architecture violation")
    state = _get_car_state(car_id)

    # Fallback: if world→2D fails, hold position briefly then escalate
    projected = project_world_to_2d(track_map, world_pos)
    if projected is None:
        state.invalid_count += 1
        if state.invalid_count > 5:
            state.phase = _ST_RECOVERING
        if state.prev_u is not None:
            return state.prev_u, state.prev_v, 0.0, False
        cu, cv = lookup_position(track_map, lap_distance)
        return cu, cv, 0.0, False

    car_u, car_v = projected
    us = track_map['us']
    vs = track_map['vs']
    n = track_map['num_points']
    track_len = track_map['track_length']

    # Compute velocity direction for direction-aware projection
    vu, vv = state.vel_u, state.vel_v
    if state.prev_world_u is not None:
        du = car_u - state.prev_world_u
        dv = car_v - state.prev_world_v
        vlen = math.sqrt(du * du + dv * dv)
        if vlen > 0.1:
            vu = du / vlen
            vv = dv / vlen
            state.vel_u = vu
            state.vel_v = vv

    if n < 2:
        if state.prev_u is not None:
            return state.prev_u, state.prev_v, 0.0, False
        cu, cv = lookup_position(track_map, lap_distance)
        return cu, cv, 0.0, False

    accepted = False

    # ── INIT: global search on first frame ──
    if state.phase == _ST_INIT:
        if car_id == 'player':
            best_seg_idx, best_proj_u, best_proj_v, best_dist_sq, best_t = \
                _find_best_segment(car_u, car_v, us, vs, n, 0, n - 1)
        elif player_seg_idx is not None:
            best_seg_idx, best_proj_u, best_proj_v, best_dist_sq, best_t = \
                _find_best_segment(car_u, car_v, us, vs, n, player_seg_idx, 20)
        else:
            center = int(lap_distance % track_len) % n
            best_seg_idx, best_proj_u, best_proj_v, best_dist_sq, best_t = \
                _find_best_segment(car_u, car_v, us, vs, n, center, 50)

        state.prev_seg_idx = best_seg_idx
        state.prev_world_u = car_u
        state.prev_world_v = car_v
        state.phase = _ST_TRACKING
        state.invalid_count = 0
        accepted = True

    # ── RECOVERING: global reset ──
    elif state.phase == _ST_RECOVERING:
        best_seg_idx, best_proj_u, best_proj_v, best_dist_sq, best_t = \
            _find_best_segment(car_u, car_v, us, vs, n, 0, n - 1)
        state.prev_seg_idx = best_seg_idx
        state.prev_world_u = car_u
        state.prev_world_v = car_v
        state.phase = _ST_TRACKING
        state.invalid_count = 0
        accepted = True

    # ── TRACKING: strict ±5 ──
    elif state.phase == _ST_TRACKING:
        center_idx = state.prev_seg_idx

        # Nearby cars close to player: use player segment
        if player_seg_idx is not None and car_id != 'player':
            ps = _get_car_state('player')
            if ps.prev_world_u is not None:
                dx = car_u - ps.prev_world_u
                dy = car_v - ps.prev_world_v
                if dx * dx + dy * dy < 400:
                    center_idx = player_seg_idx

        best_seg_idx, best_proj_u, best_proj_v, best_dist_sq, best_t = \
            _find_best_segment(car_u, car_v, us, vs, n, center_idx, 10,
                               prev_idx=state.prev_seg_idx, vel_u=vu, vel_v=vv)

        if best_dist_sq < STRICT_DIST_SQ:
            # Velocity check (player 1.5x, others 2x)
            vel_ok = True
            if state.prev_world_u is not None and speed_kmh > 0:
                mdx = car_u - state.prev_world_u
                mdy = car_v - state.prev_world_v
                actual = math.sqrt(mdx * mdx + mdy * mdy)
                factor = 1.5 if car_id == 'player' else 2.0
                expected = (speed_kmh / 3.6) * dt * factor
                if actual > max(expected, 5):
                    vel_ok = False

            if vel_ok:
                accepted = True
                state.invalid_count = 0
            else:
                state.invalid_count += 1
        else:
            state.invalid_count += 1

        if not accepted and state.invalid_count > 3:
            state.phase = _ST_UNSTABLE

    # ── UNSTABLE: relaxed ±15 ──
    elif state.phase == _ST_UNSTABLE:
        center_idx = state.prev_seg_idx

        best_seg_idx, best_proj_u, best_proj_v, best_dist_sq, best_t = \
            _find_best_segment(car_u, car_v, us, vs, n, center_idx, 30,
                               prev_idx=state.prev_seg_idx, vel_u=vu, vel_v=vv)

        if best_dist_sq < RELAXED_DIST_SQ:
            # Relaxed velocity: 3x
            vel_ok = True
            if state.prev_world_u is not None and speed_kmh > 0:
                mdx = car_u - state.prev_world_u
                mdy = car_v - state.prev_world_v
                actual = math.sqrt(mdx * mdx + mdy * mdy)
                expected = (speed_kmh / 3.6) * dt * 3.0
                if actual > max(expected, 10):
                    vel_ok = False

            if vel_ok:
                accepted = True
                state.invalid_count = 0
                state.phase = _ST_TRACKING
            else:
                state.invalid_count += 1
        else:
            state.invalid_count += 1

        if not accepted and state.invalid_count > 6:
            state.phase = _ST_RECOVERING

    # ── Update state or hold ──
    if accepted:
        # Index smoothing: blend with previous to reduce jitter
        if state.prev_seg_idx is not None:
            # Handle wrap-around
            raw_idx = best_seg_idx
            prev = state.prev_seg_idx
            delta = raw_idx - prev
            if delta > n // 2:
                delta -= n
            elif delta < -n // 2:
                delta += n
            smoothed = prev + int(round(0.3 * delta))
            best_seg_idx = smoothed % n

        state.prev_seg_idx = best_seg_idx
        state.prev_world_u = car_u
        state.prev_world_v = car_v

        # Re-project onto smoothed segment
        _, best_proj_u, best_proj_v, _, _ = \
            _find_best_segment(car_u, car_v, us, vs, n, best_seg_idx, 0)
    else:
        # Dead reckoning: predict forward motion from speed
        if state.prev_seg_idx is not None and speed_kmh > 0:
            speed_mps = speed_kmh / 3.6
            estimated_delta = speed_mps * dt
            estimated_delta = min(estimated_delta, 3.0)  # clamp to 3m max
            idx_advance = max(1, int(round(estimated_delta)))
            best_seg_idx = (state.prev_seg_idx + idx_advance) % n
            state.prev_seg_idx = best_seg_idx
        else:
            best_seg_idx = state.prev_seg_idx

        # Consecutive fallback limit: force recovery after 3
        if state.invalid_count > 3 and state.phase == _ST_TRACKING:
            state.phase = _ST_UNSTABLE

        _, best_proj_u, best_proj_v, _, _ = \
            _find_best_segment(car_u, car_v, us, vs, n, best_seg_idx, 0)

    # ── Compute lateral offset using interpolated spline normals ──
    i = best_seg_idx
    i_next = (i + 1) % n
    nus = track_map['normals_u']
    nvs = track_map['normals_v']

    # Interpolate normal along segment using t parameter
    t_param = best_t if 'best_t' in dir() else 0.5
    n0u, n0v = nus[i], nvs[i]
    n1u, n1v = nus[i_next], nvs[i_next]
    ni_u = (1 - t_param) * n0u + t_param * n1u
    ni_v = (1 - t_param) * n0v + t_param * n1v
    ni_len = math.sqrt(ni_u * ni_u + ni_v * ni_v)
    if ni_len < 1e-9:
        if state.prev_u is not None:
            return state.prev_u, state.prev_v, 0.0, False
        cu, cv = lookup_position(track_map, lap_distance)
        return cu, cv, 0.0, False
    ni_u /= ni_len
    ni_v /= ni_len

    du = car_u - best_proj_u
    dv = car_v - best_proj_v
    lateral_offset = du * ni_u + dv * ni_v

    if not accepted:
        # Dead reckoning: preserve previous lateral offset
        lateral_offset = state.prev_lateral

    hw = track_map['half_widths'][best_seg_idx] if 'half_widths' in track_map else TRACK_HALF_WIDTH_M

    # Hard offset clamp: reject extreme outliers
    if abs(lateral_offset) > hw * 2:
        if state.prev_u is not None:
            return state.prev_u, state.prev_v, state.prev_lateral, state.off_track_count >= 5
        return best_proj_u, best_proj_v, 0.0, False

    state.prev_lateral = lateral_offset

    TRACK_MARGIN = 1.5

    # Off-track: temporal filter — must persist for 5 frames
    candidate_off = abs(lateral_offset) > (hw + TRACK_MARGIN)
    if candidate_off:
        state.off_track_count += 1
    else:
        state.off_track_count = 0
    is_off_track = state.off_track_count >= 5

    # Final position: projection + interpolated normal * offset
    pos_u = best_proj_u + ni_u * lateral_offset
    pos_v = best_proj_v + ni_v * lateral_offset

    state.prev_u = pos_u
    state.prev_v = pos_v

    return pos_u, pos_v, lateral_offset, is_off_track


# ─── Stdin Reader Thread ─────────────────────────────────────────────────────

class TelemetryReader:
    """Reads telemetry JSONL from stdin in a background thread."""

    def __init__(self):
        self.latest = None
        self.lock = threading.Lock()
        self.running = True

    def start(self):
        thread = threading.Thread(target=self._read_loop, daemon=True)
        thread.start()

    def _read_loop(self):
        # Reopen stdin with line buffering (Python uses 8KB block buffer on pipes)
        try:
            stdin_fd = sys.stdin.fileno()
            line_stdin = os.fdopen(stdin_fd, 'r', buffering=1, closefd=False)
        except Exception:
            line_stdin = sys.stdin

        json_count = 0
        line_count = 0
        print("[track_map] Reader thread started, waiting for telemetry...",
              file=sys.stderr, flush=True)
        try:
            while self.running:
                line = line_stdin.readline()
                if not line:
                    break
                line_count += 1
                if not line.startswith('{'):
                    # Forward non-JSON lines to stderr (Java log messages)
                    sys.stderr.write(line)
                    sys.stderr.flush()
                    continue
                try:
                    data = json.loads(line.strip())
                    json_count += 1
                    if json_count == 1:
                        print("[track_map] First telemetry frame received!",
                              file=sys.stderr, flush=True)
                    with self.lock:
                        self.latest = data
                except json.JSONDecodeError:
                    pass
        except (KeyboardInterrupt, IOError):
            pass
        print(f"[track_map] Reader stopped. Lines: {line_count}, JSON frames: {json_count}",
              file=sys.stderr, flush=True)

    def get_latest(self):
        with self.lock:
            data = self.latest
            self.latest = None
            return data

    def stop(self):
        self.running = False


# ─── Replay Reader ──────────────────────────────────────────────────────────

class ReplayReader:
    """Reads telemetry from a recorded JSONL file with playback controls."""

    def __init__(self, path):
        self.frames = []
        self.frame_index = 0
        self.playing = False
        self.speed = 1.0
        self.wall_start = 0.0      # wall-clock time when play started
        self.data_start = 0        # timestamp (ms) of frame at play start
        self.running = True

        self._load(path)

    def _load(self, path):
        with open(path) as f:
            for line in f:
                line = line.strip()
                if not line.startswith('{'):
                    continue
                try:
                    data = json.loads(line)
                    self.frames.append(data)
                except json.JSONDecodeError:
                    pass
        if not self.frames:
            print("ERROR: No telemetry frames found in file")
            sys.exit(1)
        print(f"Loaded {len(self.frames)} frames for replay")

    def start(self):
        """Begin playback immediately."""
        self.playing = True
        self.frame_index = 0
        self._sync_clock()

    def stop(self):
        self.running = False

    def _sync_clock(self):
        """Sync wall clock to current frame position."""
        self.wall_start = time.time()
        self.data_start = self.frames[self.frame_index].get('timestamp', 0)

    def get_latest(self):
        """Return the current frame based on playback timing."""
        if not self.frames:
            return None

        if self.playing:
            elapsed_wall = time.time() - self.wall_start
            elapsed_data = elapsed_wall * self.speed * 1000  # convert to ms
            target_ts = self.data_start + elapsed_data

            # Advance frame_index to match target timestamp
            while (self.frame_index < len(self.frames) - 1 and
                   self.frames[self.frame_index + 1].get('timestamp', 0) <= target_ts):
                self.frame_index += 1

            # Auto-pause at end
            if self.frame_index >= len(self.frames) - 1:
                self.playing = False

        return self.frames[self.frame_index]

    def toggle_play(self):
        if self.playing:
            self.playing = False
        else:
            # If at end, restart from beginning
            if self.frame_index >= len(self.frames) - 1:
                self.frame_index = 0
            self.playing = True
            self._sync_clock()

    def set_speed(self, speed):
        # Re-sync clock so speed change doesn't cause a jump
        if self.playing:
            self._sync_clock()
        self.speed = speed

    def seek(self, fraction):
        """Seek to a fraction (0.0–1.0) of the recording."""
        fraction = max(0.0, min(1.0, fraction))
        self.frame_index = int(fraction * (len(self.frames) - 1))
        self._sync_clock()

    def skip_seconds(self, delta_s):
        """Skip forward/backward by delta_s seconds of recording time."""
        if not self.frames:
            return
        current_ts = self.frames[self.frame_index].get('timestamp', 0)
        target_ts = current_ts + delta_s * 1000  # ms

        if delta_s > 0:
            while (self.frame_index < len(self.frames) - 1 and
                   self.frames[self.frame_index].get('timestamp', 0) < target_ts):
                self.frame_index += 1
        else:
            while (self.frame_index > 0 and
                   self.frames[self.frame_index].get('timestamp', 0) > target_ts):
                self.frame_index -= 1

        self._sync_clock()

    def progress(self):
        """Return playback progress as 0.0–1.0."""
        if len(self.frames) <= 1:
            return 0.0
        return self.frame_index / (len(self.frames) - 1)

    def total_duration_s(self):
        """Total recording duration in seconds."""
        if len(self.frames) < 2:
            return 0.0
        t0 = self.frames[0].get('timestamp', 0)
        t1 = self.frames[-1].get('timestamp', 0)
        return (t1 - t0) / 1000.0

    def current_time_s(self):
        """Current playback position in seconds from start."""
        if not self.frames:
            return 0.0
        t0 = self.frames[0].get('timestamp', 0)
        tc = self.frames[self.frame_index].get('timestamp', 0)
        return (tc - t0) / 1000.0

    def frame_count(self):
        return len(self.frames)


def format_time(seconds):
    """Format seconds as MM:SS."""
    m = int(seconds) // 60
    s = int(seconds) % 60
    return f"{m:02d}:{s:02d}"


# ─── GUI Application ─────────────────────────────────────────────────────────

class TrackMapApp:
    """Tkinter application showing live track map with zoom/pan."""

    CANVAS_W = 800
    CANVAS_H = 600
    BG_COLOR = '#1a1a2e'
    TRACK_COLOR = '#4a4a6a'
    CAR_COLOR = '#ff3333'
    CAR_RADIUS = 6
    OTHER_CAR_COLOR = '#3399ff'
    OTHER_CAR_RADIUS = 4
    START_COLOR = '#ffffff'
    HUD_COLOR = '#cccccc'
    UPDATE_MS = 16   # ~60 Hz render rate
    MAX_OTHER_CARS = 21
    ZOOM_FACTOR = 1.2
    PROGRESS_BAR_H = 8
    PROGRESS_BG = '#333355'
    PROGRESS_FG = '#ff5555'
    STATS_W = 300
    STATS_SEP_COLOR = '#444466'

    def __init__(self, track_map, reader=None, replay_mode=False, debug=False):
        self.track_map = track_map
        self.reader = reader if reader else TelemetryReader()
        self.replay_mode = replay_mode
        self.debug = debug
        self.debug_frame_count = 0
        self.follow_player = False
        # Collision/state tracking for Feature 2
        self.prev_speed = 0
        self.prev_damage = 0      # previous total damage for change detection
        self.prev_session_time = 0 # for real dt computation
        # Interpolation: prev/curr per car — (seg_idx, offset, timestamp, off_track)
        self._interp_prev = {}
        self._interp_curr = {}
        self._last_packet_time = 0
        self.collision_frames = 0  # frames remaining in collision state
        self.speed_history = []    # last ~10 frames for sustained decel check
        self.needs_redraw = False
        self.drag_start = None
        self.last_data = None

        self.transform = CoordTransform(
            track_map['us'], track_map['vs'],
            self.CANVAS_W, self.CANVAS_H
        )

        # Build GUI
        self.root = tk.Tk()
        title = 'F1 2025 Race Replay' if replay_mode else 'F1 2025 Track Map'
        self.root.title(title)
        self.root.configure(bg=self.BG_COLOR)
        self.root.resizable(True, True)

        # Bring window to front on macOS
        self.root.lift()
        self.root.attributes('-topmost', True)
        self.root.after(100, lambda: self.root.attributes('-topmost', False))

        self.main_frame = tk.Frame(self.root, bg=self.BG_COLOR)
        self.main_frame.pack(fill=tk.BOTH, expand=True)

        self.canvas = tk.Canvas(
            self.main_frame,
            width=self.CANVAS_W,
            height=self.CANVAS_H,
            bg=self.BG_COLOR,
            highlightthickness=0
        )
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.stats_canvas = tk.Canvas(
            self.main_frame,
            width=self.STATS_W,
            bg=self.BG_COLOR,
            highlightthickness=0
        )
        self.stats_canvas.pack(side=tk.RIGHT, fill=tk.Y)

        # Bind events
        self.canvas.bind('<Configure>', self._on_resize)
        self.canvas.bind('<MouseWheel>', self._on_scroll)          # macOS/Windows
        self.canvas.bind('<Button-4>', self._on_scroll_up)         # Linux
        self.canvas.bind('<Button-5>', self._on_scroll_down)       # Linux
        self.canvas.bind('<ButtonPress-1>', self._on_click)
        self.canvas.bind('<B1-Motion>', self._on_drag)
        self.canvas.bind('<ButtonRelease-1>', self._on_drag_end)
        self.root.bind('<Key-r>', self._on_reset)
        self.root.bind('<Key-R>', self._on_reset)
        self.root.bind('<Key-f>', self._on_toggle_follow)
        self.root.bind('<Key-F>', self._on_toggle_follow)
        self.root.bind('<Key-plus>', self._on_zoom_in_key)
        self.root.bind('<Key-equal>', self._on_zoom_in_key)
        self.root.bind('<Key-minus>', self._on_zoom_out_key)

        # Replay-specific bindings
        if self.replay_mode:
            self.root.bind('<space>', self._on_replay_toggle)
            self.root.bind('<Left>', self._on_replay_back)
            self.root.bind('<Right>', self._on_replay_forward)
            self.root.bind('<Key-1>', lambda e: self._on_replay_speed(1.0))
            self.root.bind('<Key-2>', lambda e: self._on_replay_speed(2.0))
            self.root.bind('<Key-3>', lambda e: self._on_replay_speed(4.0))
            self.root.bind('<Key-4>', lambda e: self._on_replay_speed(0.5))

        # Initial draw
        self._full_redraw()

    def _full_redraw(self):
        """Redraw everything on canvas."""
        self.canvas.delete('all')
        self._draw_track()

        # Other car markers
        self.other_car_markers = []
        self.other_car_labels = []
        for _ in range(self.MAX_OTHER_CARS):
            marker = self.canvas.create_oval(
                -20, -20, -20, -20,
                fill=self.OTHER_CAR_COLOR, outline='#66bbff', width=1
            )
            label = self.canvas.create_text(
                -20, -20, text='', fill='#99ccff',
                font=('Courier', 8), anchor='s'
            )
            self.other_car_markers.append(marker)
            self.other_car_labels.append(label)

        # Player marker
        self.car_marker = self.canvas.create_oval(
            0, 0, 0, 0, fill=self.CAR_COLOR, outline='#ff6666', width=2
        )

        # HUD text (fixed position, not affected by zoom)
        self.hud_text = self.canvas.create_text(
            10, 10, anchor='nw', fill=self.HUD_COLOR,
            font=('Courier', 14, 'bold'), text='Waiting for telemetry...'
        )

        # Zoom info
        zoom_pct = int(self.transform.zoom * 100)
        follow_str = '  [F]ollow ON' if self.follow_player else ''
        self.zoom_text = self.canvas.create_text(
            self.CANVAS_W - 10, 10, anchor='ne', fill='#555577',
            font=('Courier', 10),
            text=f'Zoom: {zoom_pct}%{follow_str}  [R]eset  Scroll=Zoom  Drag=Pan'
        )

        # Progress bar (replay mode)
        if self.replay_mode:
            bar_y = self.CANVAS_H - 30
            self.progress_bg = self.canvas.create_rectangle(
                0, bar_y, self.CANVAS_W, bar_y + self.PROGRESS_BAR_H,
                fill=self.PROGRESS_BG, outline='', width=0
            )
            self.progress_fill = self.canvas.create_rectangle(
                0, bar_y, 0, bar_y + self.PROGRESS_BAR_H,
                fill=self.PROGRESS_FG, outline='', width=0
            )
            # Replay status text (below HUD, left side)
            self.replay_text = self.canvas.create_text(
                10, 30, anchor='nw', fill='#aaaacc',
                font=('Courier', 11),
                text=''
            )
        else:
            self.progress_bg = None
            self.progress_fill = None
            self.replay_text = None

        # Track name
        track_name = get_track_name_safe(self.track_map.get('track_id'))
        bottom_y = self.CANVAS_H - 45 if self.replay_mode else self.CANVAS_H - 15
        self.title_text = self.canvas.create_text(
            self.CANVAS_W // 2, bottom_y,
            anchor='s', fill='#666688',
            font=('Courier', 11), text=track_name
        )

        self.needs_redraw = False
        self._draw_stats(self.last_data)

    def _draw_track(self):
        """Draw the track as a filled ribbon with actual width."""
        us = self.track_map['us']
        vs = self.track_map['vs']
        nus = self.track_map['normals_u']
        nvs = self.track_map['normals_v']
        hws = self.track_map['half_widths']

        n = len(us)
        step = max(1, n // 1000)

        left_coords = []
        right_coords = []
        center_coords = []

        for i in range(0, n, step):
            nu, nv = nus[i], nvs[i]
            hw = hws[i]
            lu, lv = us[i] - nu * hw, vs[i] - nv * hw
            ru, rv = us[i] + nu * hw, vs[i] + nv * hw

            lcx, lcy = self.transform.to_canvas(lu, lv)
            rcx, rcy = self.transform.to_canvas(ru, rv)
            ccx, ccy = self.transform.to_canvas(us[i], vs[i])

            left_coords.extend([lcx, lcy])
            right_coords.extend([rcx, rcy])
            center_coords.extend([ccx, ccy])

        # Close the loops
        nu0, nv0 = nus[0], nvs[0]
        hw0 = hws[0]
        for coords_list, sign in [(left_coords, -1), (right_coords, 1)]:
            eu, ev = us[0] + sign * nu0 * hw0, vs[0] + sign * nv0 * hw0
            ecx, ecy = self.transform.to_canvas(eu, ev)
            coords_list.extend([ecx, ecy])
        ccx, ccy = self.transform.to_canvas(us[0], vs[0])
        center_coords.extend([ccx, ccy])

        if len(left_coords) >= 4 and len(right_coords) >= 4:
            # Build polygon: left edge forward, then right edge reversed
            flat_right_rev = []
            for i in range(len(right_coords) - 2, -1, -2):
                flat_right_rev.extend([right_coords[i], right_coords[i + 1]])
            poly = left_coords + flat_right_rev

            self.canvas.create_polygon(
                *poly, fill='#2a2a4a', outline='', width=0
            )

            # Track edges
            edge_w = max(1, int(1.5 * min(self.transform.zoom, 4)))
            self.canvas.create_line(
                *left_coords, fill='#5a5a7a', width=edge_w,
                smooth=True, capstyle='round'
            )
            self.canvas.create_line(
                *right_coords, fill='#5a5a7a', width=edge_w,
                smooth=True, capstyle='round'
            )

            # Centerline (dashed)
            center_w = max(1, int(1 * min(self.transform.zoom, 3)))
            self.canvas.create_line(
                *center_coords, fill='#3a3a5a', width=center_w,
                smooth=True, dash=(4, 8)
            )

        # Start/finish marker
        sx, sy = self.transform.to_canvas(us[0], vs[0])
        r = max(3, int(4 * min(self.transform.zoom, 3)))
        self.canvas.create_oval(
            sx - r, sy - r, sx + r, sy + r,
            fill=self.START_COLOR, outline=self.START_COLOR
        )
        self.canvas.create_text(
            sx + r + 4, sy - r - 2, anchor='sw', fill=self.START_COLOR,
            font=('Courier', 9), text='S/F'
        )

        # Corner number labels on track perimeter
        corners = self.track_map.get('corners', [])
        font_size = max(8, min(12, int(10 * min(self.transform.zoom, 3))))
        for corner in corners:
            cx, cy = self.transform.to_canvas(corner['u'], corner['v'])
            self.canvas.create_text(
                cx, cy, anchor='center', fill='#e0a040',
                font=('Courier', font_size, 'bold'),
                text=str(corner['id'] + 1)
            )

    # ─── Stats Panel ─────────────────────────────────────────────────────

    def _draw_stats(self, data):
        """Draw the telemetry stats panel."""
        c = self.stats_canvas
        c.delete('all')
        w = self.STATS_W
        h = max(int(c.winfo_height()), self.CANVAS_H)

        # Separator line
        c.create_line(0, 0, 0, h, fill=self.STATS_SEP_COLOR, width=1)

        if not data:
            c.create_text(w // 2, h // 2, anchor='center',
                          fill='#555577', font=('Courier', 11),
                          text='Waiting for\ntelemetry...')
            return

        player = data.get('player', {})
        meta = data.get('meta', {})
        y = 8
        mx = 15  # left margin
        bw = w - 30  # bar width

        # ── Speed / Gear ──
        speed = player.get('speed', 0)
        gear = player.get('gear', 0)
        gear_str = 'N' if gear == 0 else ('R' if gear < 0 else str(gear))

        c.create_text(w // 2, y, anchor='n', fill='#ffffff',
                      font=('Courier', 28, 'bold'), text=f'{speed}')
        y += 36
        c.create_text(w // 2, y, anchor='n', fill='#777799',
                      font=('Courier', 9), text='km/h')
        y += 16
        c.create_text(w // 2, y, anchor='n', fill='#ffcc00',
                      font=('Courier', 16, 'bold'), text=f'GEAR {gear_str}')
        y += 28

        # ── Throttle / Brake / Steering bars ──
        bar_h = 12
        for label, val, color, centered in [
            ('THR', player.get('throttle', 0.0), '#00cc44', False),
            ('BRK', player.get('brake', 0.0), '#ff3333', False),
            ('STR', player.get('steering', 0.0), '#4488ff', True),
        ]:
            c.create_text(mx, y + bar_h // 2, anchor='w', fill='#666688',
                          font=('Courier', 8), text=label)
            bx = mx + 30
            bw2 = w - bx - mx
            # Background
            c.create_rectangle(bx, y, bx + bw2, y + bar_h,
                               fill='#222240', outline='#333355', width=1)
            if centered:
                # Center-based bar for steering
                mid = bx + bw2 // 2
                fill_w = int(abs(val) * bw2 / 2)
                if val < 0:
                    c.create_rectangle(mid - fill_w, y + 1, mid, y + bar_h - 1,
                                       fill=color, outline='')
                else:
                    c.create_rectangle(mid, y + 1, mid + fill_w, y + bar_h - 1,
                                       fill=color, outline='')
                c.create_line(mid, y, mid, y + bar_h, fill='#555577')
                c.create_text(bx + bw2 + 4, y + bar_h // 2, anchor='w',
                              fill='#888899', font=('Courier', 7),
                              text=f'{val:+.2f}')
            else:
                fill_w = int(val * bw2)
                c.create_rectangle(bx, y + 1, bx + fill_w, y + bar_h - 1,
                                   fill=color, outline='')
                c.create_text(bx + bw2 + 4, y + bar_h // 2, anchor='w',
                              fill='#888899', font=('Courier', 7),
                              text=f'{val:.0%}')
            y += bar_h + 4
        y += 4

        # ── DRS / ERS indicators ──
        drs = player.get('drs', 0)
        drs_allowed = player.get('drsAllowed', 0)
        ers_mode = player.get('ersDeployMode', 0)

        box_w = (w - 3 * mx) // 2
        box_h = 22

        # DRS
        drs_col = '#00ff00' if drs else ('#ffcc00' if drs_allowed else '#444466')
        drs_txt = 'DRS ON' if drs else ('DRS RDY' if drs_allowed else 'DRS')
        drs_fill = drs_col if drs else '#1a1a2e'
        drs_fg = '#000000' if drs else drs_col
        c.create_rectangle(mx, y, mx + box_w, y + box_h,
                           fill=drs_fill, outline=drs_col, width=1)
        c.create_text(mx + box_w // 2, y + box_h // 2, anchor='center',
                      fill=drs_fg, font=('Courier', 9, 'bold'), text=drs_txt)

        # ERS
        ers_name = ERS_MODE_NAMES.get(ers_mode, str(ers_mode))
        ers_col = ERS_MODE_COLORS.get(ers_mode, '#444466')
        ex = w - mx - box_w
        c.create_rectangle(ex, y, ex + box_w, y + box_h,
                           fill='#1a1a2e', outline=ers_col, width=1)
        c.create_text(ex + box_w // 2, y + box_h // 2, anchor='center',
                      fill=ers_col, font=('Courier', 9, 'bold'),
                      text=f'ERS {ers_name}')
        y += box_h + 4

        # ERS energy bar
        ers_energy = player.get('ersStoreEnergy', 0.0)
        ers_pct = min(1.0, ers_energy / ERS_MAX_ENERGY) if ERS_MAX_ENERGY > 0 else 0
        c.create_text(mx, y + bar_h // 2, anchor='w', fill='#666688',
                      font=('Courier', 8), text='ERS')
        ebx = mx + 30
        ebw = w - ebx - mx
        c.create_rectangle(ebx, y, ebx + ebw, y + bar_h,
                           fill='#222240', outline='#333355', width=1)
        c.create_rectangle(ebx, y + 1, ebx + int(ers_pct * ebw), y + bar_h - 1,
                           fill='#9933ff', outline='')
        c.create_text(ebx + ebw + 4, y + bar_h // 2, anchor='w',
                      fill='#888899', font=('Courier', 7),
                      text=f'{ers_pct:.0%}')
        y += bar_h + 10

        # ── G-Force plot ──
        c.create_text(w // 2, y, anchor='n', fill='#8888aa',
                      font=('Courier', 9, 'bold'), text='G-FORCE')
        y += 16
        g_lat = player.get('gForceLateral', 0.0)
        g_lon = player.get('gForceLongitudinal', 0.0)
        gf_cx = w // 2
        gf_r = 40
        gf_cy = y + gf_r

        # Circle + crosshairs
        c.create_oval(gf_cx - gf_r, gf_cy - gf_r, gf_cx + gf_r, gf_cy + gf_r,
                      outline='#333355', width=1)
        c.create_line(gf_cx - gf_r, gf_cy, gf_cx + gf_r, gf_cy, fill='#2a2a44')
        c.create_line(gf_cx, gf_cy - gf_r, gf_cx, gf_cy + gf_r, fill='#2a2a44')

        # G-force dot (5G = full radius)
        max_g = 5.0
        dx = (g_lat / max_g) * gf_r
        dy = (-g_lon / max_g) * gf_r
        dot_r = 4
        c.create_oval(gf_cx + dx - dot_r, gf_cy + dy - dot_r,
                      gf_cx + dx + dot_r, gf_cy + dy + dot_r,
                      fill='#ff3333', outline='#ff6666')
        c.create_text(gf_cx, gf_cy + gf_r + 8, anchor='n', fill='#666688',
                      font=('Courier', 8),
                      text=f'Lat:{g_lat:+.1f}G  Lon:{g_lon:+.1f}G')
        y = gf_cy + gf_r + 24

        # ── Tyres ──
        c.create_text(w // 2, y, anchor='n', fill='#8888aa',
                      font=('Courier', 9, 'bold'), text='TYRES')
        y += 16

        tyre_wear = player.get('tyreWear', {})
        tyre_surf = player.get('tyreSurfaceTemp', [0, 0, 0, 0])
        # Arrays are [RL, RR, FL, FR] from F1 spec
        if isinstance(tyre_wear, dict):
            wear = [tyre_wear.get('frontLeft', 0), tyre_wear.get('frontRight', 0),
                    tyre_wear.get('rearLeft', 0), tyre_wear.get('rearRight', 0)]
        else:
            wear = [0, 0, 0, 0]
        # Surface temps: map from [RL,RR,FL,FR] to [FL,FR,RL,RR]
        if len(tyre_surf) >= 4:
            temps = [tyre_surf[2], tyre_surf[3], tyre_surf[0], tyre_surf[1]]
        else:
            temps = [0, 0, 0, 0]

        tw = 58
        th = 36
        gap = 16
        lx = w // 2 - tw - gap // 2
        rx = w // 2 + gap // 2
        labels = ['FL', 'FR', 'RL', 'RR']
        positions = [(lx, y), (rx, y), (lx, y + th + 4), (rx, y + th + 4)]

        for idx, (tx, ty) in enumerate(positions):
            wv = wear[idx]
            tv = temps[idx]
            # Wear color
            if wv < 30:
                wc = '#00cc44'
            elif wv < 60:
                wc = '#ffcc00'
            else:
                wc = '#ff3333'
            # Temp color
            if tv < 80:
                tc_col = '#3399ff'
            elif tv < 100:
                tc_col = '#00cc44'
            elif tv < 110:
                tc_col = '#ffcc00'
            else:
                tc_col = '#ff3333'

            c.create_rectangle(tx, ty, tx + tw, ty + th,
                               fill='#222240', outline='#333355', width=1)
            c.create_text(tx + tw // 2, ty + 10, anchor='center',
                          fill=wc, font=('Courier', 10, 'bold'),
                          text=f'{labels[idx]} {wv:.0f}%')
            c.create_text(tx + tw // 2, ty + 26, anchor='center',
                          fill=tc_col, font=('Courier', 8),
                          text=f'{tv}\u00b0C')

        y = positions[2][1] + th + 6

        # Compound + age
        compound_vis = player.get('tyreCompoundVisual', 0)
        tyre_age = player.get('tyresAgeLaps', 0)
        cname, ccol = COMPOUND_NAMES.get(compound_vis, (f'C{compound_vis}', '#aaaaaa'))
        c.create_text(w // 2, y, anchor='n', fill=ccol,
                      font=('Courier', 9, 'bold'),
                      text=f'{cname}  Age: {tyre_age} laps')
        y += 18

        # ── Front Wing Damage ──
        fl_wing = player.get('frontLeftWingDamage', 0)
        fr_wing = player.get('frontRightWingDamage', 0)
        avg_wing = (fl_wing + fr_wing) / 2.0

        c.create_text(w // 2, y, anchor='n', fill='#8888aa',
                      font=('Courier', 9, 'bold'), text='FRONT WING')
        y += 16

        # Color coding: 0-10% green, 10-40% yellow, 40%+ red
        if avg_wing <= 10:
            wing_col = '#00cc44'
        elif avg_wing <= 40:
            wing_col = '#ffcc00'
        else:
            wing_col = '#ff3333'

        # Bar
        c.create_text(mx, y + bar_h // 2, anchor='w', fill='#666688',
                      font=('Courier', 8), text='DMG')
        wbx = mx + 30
        wbw = w - wbx - mx
        c.create_rectangle(wbx, y, wbx + wbw, y + bar_h,
                           fill='#222240', outline='#333355', width=1)
        fill_w = int(min(avg_wing / 100.0, 1.0) * wbw)
        if fill_w > 0:
            c.create_rectangle(wbx, y + 1, wbx + fill_w, y + bar_h - 1,
                               fill=wing_col, outline='')
        c.create_text(wbx + wbw + 4, y + bar_h // 2, anchor='w',
                      fill='#888899', font=('Courier', 7),
                      text=f'{avg_wing:.0f}%')
        y += bar_h + 4

        # L/R detail
        c.create_text(mx + 10, y, anchor='w', fill='#777799',
                      font=('Courier', 8), text=f'FL: {fl_wing:.0f}%')
        c.create_text(w // 2 + 10, y, anchor='w', fill='#777799',
                      font=('Courier', 8), text=f'FR: {fr_wing:.0f}%')
        y += 16

        # ── Other Damage ──
        c.create_text(w // 2, y, anchor='n', fill='#8888aa',
                      font=('Courier', 9, 'bold'), text='DAMAGE')
        y += 16
        rear_wing = player.get('rearWingDamage', 0)
        for lbl, val in [('R.Wing', rear_wing),
                         ('Floor', player.get('floorDamage', 0)),
                         ('Diffuser', player.get('diffuserDamage', 0)),
                         ('Sidepod', player.get('sidepodDamage', 0))]:
            if val == 0:
                dc = '#00cc44'
                dt = 'OK'
            else:
                dc = '#ffcc00' if val < 50 else '#ff3333'
                dt = f'{val:.0f}%'
            c.create_text(mx + 10, y, anchor='w', fill='#777799',
                          font=('Courier', 8), text=f'{lbl}:')
            c.create_text(mx + 80, y, anchor='w', fill=dc,
                          font=('Courier', 8, 'bold'), text=dt)
            y += 14
        y += 6

        # ── Flags / Safety Car / Weather ──
        sc = meta.get('safety_car', 0)
        sc_name = SC_NAMES.get(sc, '')
        flag = player.get('vehicleFiaFlags', 0)
        flag_col = FLAG_COLORS.get(flag, '#444466')
        weather = meta.get('weather', 0)
        weather_name = WEATHER_NAMES.get(weather, '')
        track_temp = meta.get('track_temp', 0)
        air_temp = meta.get('air_temp', 0)

        if sc_name:
            sc_col = '#ffcc00' if sc == 2 else '#ff3333'
            c.create_rectangle(mx, y, w - mx, y + 20,
                               fill='#1a1a2e', outline=sc_col, width=1)
            c.create_text(w // 2, y + 10, anchor='center',
                          fill=sc_col, font=('Courier', 10, 'bold'),
                          text=sc_name)
            y += 24

        if flag > 0:
            flag_names = {1: 'GREEN', 2: 'BLUE', 3: 'YELLOW', 4: 'RED'}
            fname = flag_names.get(flag, f'FLAG {flag}')
            c.create_text(w // 2, y, anchor='n', fill=flag_col,
                          font=('Courier', 9, 'bold'), text=fname)
            y += 16

        c.create_text(w // 2, y, anchor='n', fill='#555577',
                      font=('Courier', 8),
                      text=f'{weather_name}  Track:{track_temp}\u00b0C  Air:{air_temp}\u00b0C')
        y += 18

        # ── Mini Leaderboard ──
        all_cars_lb = data.get('allCars', [])
        nearby_gaps = {c.get('carIndex'): c.get('gap', 0) for c in data.get('nearbyCars', [])}
        player_pos = player.get('position', 0)

        if all_cars_lb and player_pos > 0:
            c.create_text(w // 2, y, anchor='n', fill='#8888aa',
                          font=('Courier', 9, 'bold'), text='LEADERBOARD')
            y += 16

            # Sort all cars by position ascending (P1, P2, P3...)
            sorted_cars = sorted(
                [c for c in all_cars_lb if c.get('position', 0) > 0],
                key=lambda c: c['position']
            )

            # Split into ahead (lower position) and behind (higher position)
            ahead = []
            behind = []
            for car in sorted_cars:
                car_pos = car.get('position', 0)
                if car_pos == player_pos:
                    continue
                car_idx = car.get('carIndex', -1)
                gap = abs(nearby_gaps.get(car_idx, 0))
                if car_pos < player_pos:
                    ahead.append({'position': car_pos, 'gap': gap})
                else:
                    behind.append({'position': car_pos, 'gap': gap})

            # Take closest 3 ahead (highest positions = closest to player) and 3 behind
            ahead = ahead[-3:]  # last 3 = closest positions to player
            behind = behind[:3] # first 3 = closest positions to player

            row_h = 16
            font_lb = ('Courier', 8)

            for car in ahead:
                pos = car['position']
                gap = car['gap']
                gap_str = f'+{gap:.2f}' if gap > 0 else ''
                c.create_text(mx, y, anchor='w', fill='#888899',
                              font=font_lb, text=f'P{pos}')
                c.create_text(w - mx, y, anchor='e', fill='#aaaacc',
                              font=font_lb, text=gap_str)
                y += row_h

            # Player row
            c.create_rectangle(mx - 2, y - 2, w - mx + 2, y + row_h - 2,
                               fill='#2a2a4a', outline='#4444aa', width=1)
            c.create_text(mx, y, anchor='w', fill='#ffffff',
                          font=('Courier', 8, 'bold'), text=f'P{player_pos}')
            c.create_text(w - mx, y, anchor='e', fill='#ffffff',
                          font=('Courier', 8, 'bold'), text='YOU')
            y += row_h

            for car in behind:
                pos = car['position']
                gap = car['gap']
                gap_str = f'-{gap:.2f}' if gap > 0 else ''
                c.create_text(mx, y, anchor='w', fill='#888899',
                              font=font_lb, text=f'P{pos}')
                c.create_text(w - mx, y, anchor='e', fill='#aaaacc',
                              font=font_lb, text=gap_str)
                y += row_h

    # ─── Event Handlers ───────────────────────────────────────────────────

    def _on_resize(self, event):
        new_w = event.width
        new_h = event.height
        if new_w < 200 or new_h < 150:
            return
        self.CANVAS_W = new_w
        self.CANVAS_H = new_h
        self.transform.canvas_w = new_w
        self.transform.canvas_h = new_h
        self.needs_redraw = True

    def _on_scroll(self, event):
        # macOS: event.delta is +/- 120 (or multiples)
        if event.delta > 0:
            self.transform.zoom_at(self.ZOOM_FACTOR, event.x, event.y)
        else:
            self.transform.zoom_at(1.0 / self.ZOOM_FACTOR, event.x, event.y)
        self.needs_redraw = True

    def _on_scroll_up(self, event):
        self.transform.zoom_at(self.ZOOM_FACTOR, event.x, event.y)
        self.needs_redraw = True

    def _on_scroll_down(self, event):
        self.transform.zoom_at(1.0 / self.ZOOM_FACTOR, event.x, event.y)
        self.needs_redraw = True

    def _on_click(self, event):
        # Check if click is on the progress bar (replay mode)
        if self.replay_mode and isinstance(self.reader, ReplayReader):
            bar_y = self.CANVAS_H - 30
            if bar_y <= event.y <= bar_y + self.PROGRESS_BAR_H:
                fraction = event.x / self.CANVAS_W
                self.reader.seek(fraction)
                return
        self.drag_start = (event.x, event.y)

    def _on_drag(self, event):
        if self.drag_start:
            dx = event.x - self.drag_start[0]
            dy = event.y - self.drag_start[1]
            self.transform.pan_x += dx
            self.transform.pan_y += dy
            self.drag_start = (event.x, event.y)
            self.needs_redraw = True

    def _on_drag_end(self, event):
        self.drag_start = None

    def _on_reset(self, event=None):
        self.transform.reset(self.CANVAS_W, self.CANVAS_H)
        self.follow_player = False
        self.needs_redraw = True

    def _on_toggle_follow(self, event=None):
        self.follow_player = not self.follow_player
        self.needs_redraw = True

    def _on_zoom_in_key(self, event=None):
        cx, cy = self.CANVAS_W / 2, self.CANVAS_H / 2
        self.transform.zoom_at(self.ZOOM_FACTOR, cx, cy)
        self.needs_redraw = True

    def _on_zoom_out_key(self, event=None):
        cx, cy = self.CANVAS_W / 2, self.CANVAS_H / 2
        self.transform.zoom_at(1.0 / self.ZOOM_FACTOR, cx, cy)
        self.needs_redraw = True

    # ─── Replay Controls ─────────────────────────────────────────────────

    def _on_replay_toggle(self, event=None):
        if isinstance(self.reader, ReplayReader):
            self.reader.toggle_play()

    def _on_replay_back(self, event=None):
        if isinstance(self.reader, ReplayReader):
            self.reader.skip_seconds(-5)

    def _on_replay_forward(self, event=None):
        if isinstance(self.reader, ReplayReader):
            self.reader.skip_seconds(5)

    def _on_replay_speed(self, speed):
        if isinstance(self.reader, ReplayReader):
            self.reader.set_speed(speed)

    def _interp_pos(self, car_id, now):
        """Interpolate seg_idx and offset, reconstruct from track normals."""
        curr = self._interp_curr.get(car_id)
        prev = self._interp_prev.get(car_id)
        if curr is None:
            return 0, 0

        c_idx, c_off, t1, _ = curr
        if prev is None:
            alpha = 1.0
            p_idx, p_off, t0 = c_idx, c_off, t1
        else:
            p_idx, p_off, t0, _ = prev
            dt = t1 - t0
            if dt > 0:
                alpha = max(0.0, min(1.0, (now - t0) / dt))
            else:
                alpha = 1.0

        # Interpolate index (handle wrap-around)
        n = self.track_map['num_points']
        delta = c_idx - p_idx
        if delta > n // 2:
            delta -= n
        elif delta < -n // 2:
            delta += n
        idx = int(round(p_idx + alpha * delta)) % n

        # Interpolate offset
        offset = p_off + alpha * (c_off - p_off)

        # Clamp to track width
        hws = self.track_map['half_widths']
        hw = hws[idx]
        offset = max(-hw, min(hw, offset))

        # Reconstruct from track centerline + stored normals
        us = self.track_map['us']
        vs = self.track_map['vs']
        nus = self.track_map['normals_u']
        nvs = self.track_map['normals_v']

        pos_u = us[idx] + nus[idx] * offset
        pos_v = vs[idx] + nvs[idx] * offset
        return pos_u, pos_v

    # ─── Telemetry Processing (ONLY on new UDP data) ────────────────────

    def _process_telemetry(self, data):
        """Process new telemetry: compute projections and update interp state.
        Called ONLY when new data arrives (~30 Hz). NO rendering here."""
        player = data.get('player', {})
        speed = player.get('speed', 0)
        lap_dist = player.get('lapDistance', 0.0)

        # Compute real dt
        session_time = data.get('sessionTime', 0)
        if self.prev_session_time > 0 and session_time > self.prev_session_time:
            real_dt = max(0.01, min(0.05, session_time - self.prev_session_time))
        else:
            real_dt = 1.0 / 30.0
        self.prev_session_time = session_time

        player_world_pos = player.get('world_pos_m')

        # Player projection
        pu, pv, player_lat, p_off = compute_track_position(
            self.track_map, player_world_pos, lap_dist,
            car_id='player', speed_kmh=speed, dt=real_dt)

        now = time.time()
        ps = _get_car_state('player')
        ps.last_seen = now
        new_s = ps.prev_seg_idx or 0
        # Clamp + smooth S at state level
        if 'player' in self._interp_curr:
            prev_s = self._interp_curr['player'][0]
            prev_off = self._interp_curr['player'][1]
            ds = new_s - prev_s
            n = self.track_map['num_points']
            if ds > n // 2: ds -= n
            elif ds < -n // 2: ds += n
            if abs(ds) > 10:
                new_s = prev_s  # reject noisy jump
            else:
                new_s = int(round(0.85 * prev_s + 0.15 * new_s)) % n
            player_lat = 0.9 * prev_off + 0.1 * player_lat
            self._interp_prev['player'] = self._interp_curr['player']
        self._interp_curr['player'] = (new_s, player_lat, now, p_off)
        self._last_packet_time = now

        # Follow player
        if self.follow_player:
            self.transform.center_on(pu, pv)
            self.needs_redraw = True

        player_seg = ps.prev_seg_idx

        # Other cars projection
        all_cars = data.get('allCars', [])
        for car in all_cars:
            car_index = car.get('carIndex', -1)
            if car_index < 0:
                continue
            cid = f'ci_{car_index}'
            car_dist = car.get('lapDistance', 0.0)
            car_world_pos = car.get('world_pos_m')
            car_speed = car.get('speed', 0)
            cu, cv, car_lat, car_off = compute_track_position(
                self.track_map, car_world_pos, car_dist,
                car_id=cid, speed_kmh=car_speed,
                dt=real_dt, player_seg_idx=player_seg)

            cs = _get_car_state(cid)
            cs.last_seen = now
            new_s = cs.prev_seg_idx or 0
            n = self.track_map['num_points']
            # Clamp + smooth S at state level
            if cid in self._interp_curr:
                prev_s = self._interp_curr[cid][0]
                prev_off = self._interp_curr[cid][1]
                ds = new_s - prev_s
                if ds > n // 2: ds -= n
                elif ds < -n // 2: ds += n
                if abs(ds) > 10:
                    new_s = prev_s
                else:
                    new_s = int(round(0.85 * prev_s + 0.15 * new_s)) % n
                car_lat = 0.9 * prev_off + 0.1 * car_lat
                self._interp_prev[cid] = self._interp_curr[cid]
            self._interp_curr[cid] = (new_s, car_lat, now, car_off)

        # Soft separation: push apart clustered cars
        car_entries = [(cid, self._interp_curr[cid][0])
                       for cid in self._interp_curr if cid != 'player']
        if len(car_entries) > 1:
            car_entries.sort(key=lambda x: x[1])
            n = self.track_map['num_points']
            for i in range(1, len(car_entries)):
                gap = car_entries[i][1] - car_entries[i-1][1]
                if gap < 0: gap += n
                if gap < 1.5:
                    cid_push = car_entries[i][0]
                    old = self._interp_curr[cid_push]
                    pushed_s = (old[0] + int((1.5 - gap) * 0.5)) % n
                    self._interp_curr[cid_push] = (pushed_s, old[1], old[2], old[3])

        # Cleanup stale cars (not seen for >3 seconds)
        STALE_TIMEOUT = 3.0
        stale_ids = [cid for cid, st in _car_states.items()
                     if cid != 'player' and now - st.last_seen > STALE_TIMEOUT]
        for cid in stale_ids:
            del _car_states[cid]
            self._interp_curr.pop(cid, None)
            self._interp_prev.pop(cid, None)

        # Collision detection (telemetry-driven, not render-driven)
        fl_wing = player.get('frontLeftWingDamage', 0)
        fr_wing = player.get('frontRightWingDamage', 0)
        rear_wing = player.get('rearWingDamage', 0)
        floor_dmg = player.get('floorDamage', 0)
        total_damage = fl_wing + fr_wing + rear_wing + floor_dmg
        if total_damage > self.prev_damage + 1:
            self.collision_frames = 30
        self.prev_damage = total_damage

        self.speed_history.append(speed)
        if len(self.speed_history) > 9:
            self.speed_history.pop(0)
        if len(self.speed_history) >= 9 and max(self.speed_history) - speed > 40:
            self.collision_frames = 30
        self.prev_speed = speed

        # Debug logging
        if self.debug:
            self.debug_frame_count += 1
            if self.debug_frame_count % 30 == 1:
                phase_names = {_ST_INIT: 'INIT', _ST_TRACKING: 'TRACK',
                               _ST_UNSTABLE: 'UNSTBL', _ST_RECOVERING: 'RECOV'}
                hw = self.track_map['half_widths'][ps.prev_seg_idx] if ps.prev_seg_idx else 0
                print(f"[DEBUG] player {phase_names.get(ps.phase, '?')}"
                      f" seg={ps.prev_seg_idx} offset={player_lat:+.1f}m"
                      f" hw={hw:.1f}m inv={ps.invalid_count} spd={speed}",
                      file=sys.stderr, flush=True)
                if abs(player_lat) < 2.0 and hw > 4.0:
                    print(f"[DEBUG] WARNING: offset < 2m with hw={hw:.1f}m"
                          f" — possible compression", file=sys.stderr, flush=True)
                # State isolation + tracking check
                if self.debug_frame_count == 1 or self.debug_frame_count % 300 == 0:
                    ids = set()
                    for cid, st in _car_states.items():
                        addr = id(st)
                        if addr in ids:
                            print(f"[DEBUG] ERROR: shared state object at {addr}!",
                                  file=sys.stderr, flush=True)
                        ids.add(addr)
                    tracked = sorted(k for k in _car_states if k != 'player')
                    print(f"[DEBUG] Tracked: {len(_car_states)} cars ({tracked})",
                          file=sys.stderr, flush=True)
                    print(f"[DEBUG] State isolation OK: {len(ids)} unique objects",
                          file=sys.stderr, flush=True)

    # ─── Render (every frame, interpolation only) ─────────────────────

    def _render_cars(self):
        """Render all cars using interpolated positions. NO projection here."""
        global _in_render_loop
        _in_render_loop = True
        try:
            self._render_cars_impl()
        finally:
            _in_render_loop = False

    def _render_cars_impl(self):
        if not self._interp_curr:
            return

        render_now = time.time()
        data = self.last_data or {}
        player = data.get('player', {})
        all_cars = data.get('allCars', [])

        # Player
        if 'player' in self._interp_curr:
            ipu, ipv = self._interp_pos('player', render_now)
            cx, cy = self.transform.to_canvas(ipu, ipv)
            r = self.CAR_RADIUS
            self.canvas.coords(self.car_marker, cx - r, cy - r, cx + r, cy + r)

            _, _, _, p_off = self._interp_curr['player']
            if self.collision_frames > 0:
                self.collision_frames -= 1
                self.canvas.itemconfig(self.car_marker,
                                       fill='#ff0000', outline='#ff4444')
            elif p_off:
                self.canvas.itemconfig(self.car_marker,
                                       fill='#ffcc00', outline='#ffee44')
            else:
                self.canvas.itemconfig(self.car_marker,
                                       fill='#ffffff', outline='#cccccc')
            self.canvas.tag_raise(self.car_marker)

            # DRS indicator
            drs_allowed = player.get('drsAllowed', 0)
            drs_active = player.get('drs', 0)
            drs_tag = 'drs_indicator'
            self.canvas.delete(drs_tag)
            if drs_active:
                dr = r + 4
                self.canvas.create_oval(
                    cx - dr, cy - dr, cx + dr, cy + dr,
                    fill='', outline='#00ff44', width=3, tags=drs_tag)
                self.canvas.create_text(
                    cx, cy - dr - 6, text='DRS', fill='#00ff44',
                    font=('Courier', 8, 'bold'), anchor='s', tags=drs_tag)
            elif drs_allowed:
                dr = r + 4
                self.canvas.create_oval(
                    cx - dr, cy - dr, cx + dr, cy + dr,
                    fill='', outline='#00aa33', width=2, dash=(3, 3),
                    tags=drs_tag)

        # Other cars
        render_cars = []
        for car in all_cars:
            car_index = car.get('carIndex', -1)
            if car_index < 0:
                continue
            cid = f'ci_{car_index}'
            if cid in self._interp_curr:
                render_cars.append((cid, car.get('position', 0)))

        for i in range(self.MAX_OTHER_CARS):
            if i < len(render_cars):
                cid, car_pos = render_cars[i]
                cu, cv = self._interp_pos(cid, render_now)
                _, _, _, car_off = self._interp_curr[cid]
                ccx, ccy = self.transform.to_canvas(cu, cv)
                r = self.OTHER_CAR_RADIUS
                self.canvas.coords(
                    self.other_car_markers[i],
                    ccx - r, ccy - r, ccx + r, ccy + r)
                self.canvas.coords(
                    self.other_car_labels[i], ccx, ccy - r - 2)
                self.canvas.itemconfig(
                    self.other_car_labels[i],
                    text=f'P{car_pos}' if car_pos else '')
                if car_off:
                    self.canvas.itemconfig(
                        self.other_car_markers[i],
                        fill='#ff9900', outline='#ffbb44')
                else:
                    self.canvas.itemconfig(
                        self.other_car_markers[i],
                        fill=self.OTHER_CAR_COLOR, outline='#66bbff')
            else:
                self.canvas.coords(
                    self.other_car_markers[i], -20, -20, -20, -20)
                self.canvas.coords(self.other_car_labels[i], -20, -20)
                self.canvas.itemconfig(self.other_car_labels[i], text='')

    # ─── Update Loop ──────────────────────────────────────────────────

    def _update(self):
        """Main loop: process telemetry if available, then render."""
        data = self.reader.get_latest()

        # Phase 1: Process new telemetry (projection) — only when data arrives
        if data:
            self.last_data = data
            self._process_telemetry(data)

        # Phase 2: Redraw track if needed
        if self.needs_redraw:
            self._full_redraw()

        # Phase 3: Render cars (interpolation only) — every frame
        self._render_cars()

        # Phase 4: UI overlays (only update on new data)
        if data:
            player = data.get('player', {})
            all_cars = data.get('allCars', [])
            position = player.get('position', 0)
            lap_num = player.get('lapNumber', 0)
            speed = player.get('speed', 0)
            gear = player.get('gear', 0)
            throttle = player.get('throttle', 0.0)
            brake = player.get('brake', 0.0)
            gear_str = 'N' if gear == 0 else ('R' if gear < 0 else str(gear))

            n_cars = len(all_cars) + 1
            hud = f"P{position}/{n_cars}  Lap {lap_num}  {speed} km/h  G{gear_str}"
            hud += f"  T:{throttle:.0%}  B:{brake:.0%}"
            self.canvas.itemconfig(self.hud_text, text=hud)

            zoom_pct = int(self.transform.zoom * 100)
            follow_str = '  [F]ollow ON' if self.follow_player else ''
            self.canvas.itemconfig(
                self.zoom_text,
                text=f'Zoom: {zoom_pct}%{follow_str}  [R]eset  Scroll=Zoom  Drag=Pan')

            if self.replay_mode and isinstance(self.reader, ReplayReader):
                progress = self.reader.progress()
                bar_y = self.CANVAS_H - 30
                fill_w = progress * self.CANVAS_W
                self.canvas.coords(
                    self.progress_bg, 0, bar_y, self.CANVAS_W, bar_y + self.PROGRESS_BAR_H)
                self.canvas.coords(
                    self.progress_fill, 0, bar_y, fill_w, bar_y + self.PROGRESS_BAR_H)
                self.canvas.tag_raise(self.progress_bg)
                self.canvas.tag_raise(self.progress_fill)

                cur = format_time(self.reader.current_time_s())
                tot = format_time(self.reader.total_duration_s())
                rstate = "Playing" if self.reader.playing else "Paused"
                spd = self.reader.speed
                spd_str = f"{spd:.1f}x" if spd != int(spd) else f"{int(spd)}x"
                self.canvas.itemconfig(
                    self.replay_text,
                    text=f"{rstate}  {cur} / {tot}  [{spd_str}]  Space=Play/Pause  \u2190\u2192=\u00b15s  1-4=Speed")

            self._draw_stats(data)

        self.root.after(self.UPDATE_MS, self._update)

    def run(self, preview_only=False):
        """Start reader thread and tkinter mainloop."""
        if preview_only:
            self.canvas.itemconfig(self.hud_text, text='Preview mode (no live data)')
            self._schedule_redraw_check()
        elif self.replay_mode:
            self.reader.start()
            self.root.after(self.UPDATE_MS, self._update)
        else:
            self.reader.start()
            self.root.after(self.UPDATE_MS, self._update)

        try:
            self.root.mainloop()
        except KeyboardInterrupt:
            pass
        finally:
            self.reader.stop()

    def _schedule_redraw_check(self):
        """Check for needed redraws in preview mode."""
        if self.needs_redraw:
            self._full_redraw()
            self.canvas.itemconfig(self.hud_text, text='Preview mode (no live data)')
            zoom_pct = int(self.transform.zoom * 100)
            self.canvas.itemconfig(
                self.zoom_text,
                text=f'Zoom: {zoom_pct}%  [R]eset  Scroll=Zoom  Drag=Pan'
            )
        self.root.after(self.UPDATE_MS, self._schedule_redraw_check)


# ─── Track Name Helper ────────────────────────────────────────────────────────

TRACK_NAMES = {
    0: "Melbourne (Australia)", 1: "Paul Ricard (France)",
    2: "Shanghai (China)", 3: "Sakhir (Bahrain)",
    4: "Catalunya (Spain)", 5: "Monaco", 6: "Montreal (Canada)",
    7: "Silverstone (Great Britain)", 8: "Hockenheim (Germany)",
    9: "Hungaroring (Hungary)", 10: "Spa (Belgium)",
    11: "Monza (Italy)", 12: "Singapore",
    13: "Suzuka (Japan)", 14: "Abu Dhabi",
    15: "Austin (USA)", 16: "Interlagos (Brazil)",
    17: "Red Bull Ring (Austria)", 18: "Sochi (Russia)",
    19: "Mexico City", 20: "Baku (Azerbaijan)",
    21: "Sakhir Short", 22: "Silverstone Short",
    23: "Austin Short", 24: "Suzuka Short",
    25: "Hanoi (Vietnam)", 26: "Zandvoort (Netherlands)",
    27: "Imola (Italy)", 28: "Portimao (Portugal)",
    29: "Jeddah (Saudi Arabia)", 30: "Miami (USA)",
    31: "Las Vegas (USA)", 32: "Losail (Qatar)",
}


COMPOUND_NAMES = {
    16: ('SOFT', '#ff3333'), 17: ('MEDIUM', '#ffcc00'), 18: ('HARD', '#ffffff'),
    7: ('INTER', '#00cc44'), 8: ('WET', '#3399ff'),
}

WEATHER_NAMES = {
    0: 'Clear', 1: 'Light Cloud', 2: 'Overcast',
    3: 'Light Rain', 4: 'Heavy Rain', 5: 'Storm',
}

SC_NAMES = {0: '', 1: 'SAFETY CAR', 2: 'VSC', 3: 'FORMATION'}

FLAG_COLORS = {
    -1: '#444466', 0: '#444466', 1: '#00cc44',
    2: '#3399ff', 3: '#ffcc00', 4: '#ff0000',
}

ERS_MODE_NAMES = {0: 'NONE', 1: 'MED', 2: 'HOTLAP', 3: 'OVERTAKE'}
ERS_MODE_COLORS = {0: '#444466', 1: '#ffcc00', 2: '#ff6600', 3: '#ff3333'}
ERS_MAX_ENERGY = 4_000_000.0  # 4 MJ


def get_track_name_safe(track_id):
    if track_id is None:
        return "Unknown Track"
    return TRACK_NAMES.get(track_id, f"Track {track_id}")


# ─── Main ────────────────────────────────────────────────────────────────────

def main():
    preview = '--preview' in sys.argv
    debug = '--debug' in sys.argv
    replay_file = None

    # Parse --replay <file>
    raw_args = sys.argv[1:]
    if '--replay' in raw_args:
        idx = raw_args.index('--replay')
        if idx + 1 < len(raw_args):
            replay_file = raw_args[idx + 1]
            raw_args = raw_args[:idx] + raw_args[idx + 2:]
        else:
            print("ERROR: --replay requires a JSONL file path")
            sys.exit(1)

    args = [a for a in raw_args if a not in ('--preview', '--debug')]

    if not args:
        print("Usage: python3 track_map_live.py <track_map.json> [options]")
        print()
        print("Options:")
        print("  --preview              Show track map only (no live data)")
        print("  --replay <file.jsonl>  Replay a recorded telemetry file")
        print("  --debug                Print lateral offsets per car to stderr")
        print()
        print("Controls:")
        print("  Scroll wheel    Zoom in/out (toward cursor)")
        print("  Click + drag    Pan the map")
        print("  +/-             Zoom in/out (center)")
        print("  R               Reset zoom to fit")
        print("  F               Follow player car (toggle)")
        print()
        print("Replay controls:")
        print("  Space           Play / pause")
        print("  Left / Right    Skip -5s / +5s")
        print("  1 / 2 / 3 / 4  Speed 1x / 2x / 4x / 0.5x")
        print("  Click bar       Seek to position")
        print()
        print("Examples:")
        print("  python3 track_map_live.py track_0_map.json --preview")
        print("  python3 track_map_live.py track_0_map.json --replay race.jsonl")
        print("  mvn -q exec:java ... 2>&1 | python3 track_map_live.py track_0_map.json")
        sys.exit(1)

    map_path = args[0]

    try:
        track_map = load_track_map(map_path)
    except FileNotFoundError:
        print(f"ERROR: Track map not found: {map_path}")
        sys.exit(1)
    except (json.JSONDecodeError, KeyError) as e:
        print(f"ERROR: Invalid track map file: {e}")
        sys.exit(1)

    print(f"Loaded track map: {track_map['num_points']} points, "
          f"{track_map['track_length']}m")

    if replay_file:
        reader = ReplayReader(replay_file)
        dur = format_time(reader.total_duration_s())
        print(f"Replay: {reader.frame_count()} frames, {dur} duration")
        print("Controls: Space=Play/Pause | Left/Right=Skip | 1-4=Speed | Scroll=Zoom | Drag=Pan")
        app = TrackMapApp(track_map, reader=reader, replay_mode=True, debug=debug)
        app.run()
    elif preview:
        print("Opening preview... (close window to exit)")
        print("Controls: Scroll=Zoom | Drag=Pan | R=Reset | +/-=Zoom")
        app = TrackMapApp(track_map, debug=debug)
        app.run(preview_only=True)
    else:
        print("Starting GUI... (close window or Ctrl+C to stop)")
        print("Controls: Scroll=Zoom | Drag=Pan | R=Reset | F=Follow | +/-=Zoom")
        app = TrackMapApp(track_map, debug=debug)
        app.run()


if __name__ == '__main__':
    main()
