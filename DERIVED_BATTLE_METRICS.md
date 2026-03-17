# Derived Battle Metrics

## Purpose

These metrics convert raw telemetry into **racecraft intelligence signals** used to analyze overtaking, defending, and battle management.

They are derived from telemetry already available in the system and should not duplicate existing pipelines.

Claude should compute these metrics every telemetry frame or over short rolling windows (1-3 seconds).

---

## Telemetry Field Reference

Available inputs from the JSONL telemetry stream (30 Hz):

### Player (`player.*`)
| Field | Type | Description |
|-------|------|-------------|
| `lapDistance` | float | Meters along track centerline (0 to track_length) |
| `speed` | int | Speed in km/h |
| `steering` | float | -1.0 (full left) to +1.0 (full right) |
| `throttle` | float | 0.0 to 1.0 |
| `brake` | float | 0.0 to 1.0 |
| `gear` | int | Current gear |
| `position` | int | Race position |
| `lapNumber` | int | Current lap |
| `world_pos_m.x/y/z` | float | 3D world position (meters) |
| `yaw` | float | Heading angle (radians) |
| `gForceLateral` | float | Lateral G-force |
| `gForceLongitudinal` | float | Longitudinal G-force |
| `drs` | int | DRS active (0/1) |
| `drsAllowed` | int | DRS permitted (0/1) |
| `ersDeployMode` | int | ERS mode (0=none, 1=med, 2=hotlap, 3=overtake) |
| `ersStoreEnergy` | float | Stored ERS energy (Joules) |
| `tyreWear.*` | float | Per-corner wear % (frontLeft, frontRight, rearLeft, rearRight) |
| `tyreSurfaceTemp` | int[] | Surface temps [RL, RR, FL, FR] in C |
| `tyreCompoundVisual` | int | 16=soft, 17=medium, 18=hard |
| `tyresAgeLaps` | int | Laps on current set |

### Nearby Cars (`nearbyCars[]`)
| Field | Type | Description |
|-------|------|-------------|
| `carIndex` | int | Car identifier |
| `position` | int | Race position |
| `gap` | double | Time gap in seconds (negative = ahead, positive = behind) |
| `world_pos_m.x/y/z` | float | 3D world position (meters) |

### All Cars (`allCars[]`)
| Field | Type | Description |
|-------|------|-------------|
| `carIndex` | int | Car identifier |
| `position` | int | Race position |
| `lapDistance` | float | Meters along track |
| `lapNumber` | int | Current lap |

### Track Map (`track_N_map.json`)
| Field | Type | Description |
|-------|------|-------------|
| `track_length_m` | int | Total track length in meters |
| `points[].s` | int | Distance along centerline (0 to track_length_m-1) |
| `points[].u` | float | 2D map coordinate (horizontal axis) |
| `points[].v` | float | 2D map coordinate (vertical axis) |

### Session Metadata (`meta.*`)
| Field | Type | Description |
|-------|------|-------------|
| `track_id` | int | Track identifier |
| `track_length` | int | Track length (meters) |
| `weather` | int | 0=clear, 1=light cloud, 2=overcast, 3=light rain, 4=heavy rain, 5=storm |
| `safety_car` | int | 0=none, 1=full SC, 2=VSC, 3=formation |

---

# Core Derived Battle Metrics

## 1. Gap to Opponent

Distance in meters between player and the target opponent along the track centerline.

**Inputs:**
- `player.lapDistance`
- `nearbyCars[target].gap` (seconds)
- `player.speed` (km/h)
- `meta.track_length` (meters)

**Formula:**
```
# Primary: use time gap and convert to distance
gap_meters = nearbyCars[target].gap * (player.speed / 3.6)

# Alternative: from lap distances (handles lap wrapping)
raw_diff = opponent.lapDistance - player.lapDistance
if raw_diff > track_length / 2:
    raw_diff -= track_length
elif raw_diff < -track_length / 2:
    raw_diff += track_length
gap_meters = raw_diff
```

**Output:** `float`, meters (negative = opponent ahead, positive = opponent behind)
**Update:** Every frame
**Dependencies:** None (base metric)

---

## 2. Relative Speed

Speed difference between player and opponent.

**Inputs:**
- `player.speed` (km/h)
- Opponent speed — estimated from frame-to-frame `lapDistance` change:
  `opponent_speed = (opponent.lapDistance[t] - opponent.lapDistance[t-1]) / dt`

**Formula:**
```
# Opponent speed estimated from position delta
opponent_speed_ms = delta_lapDistance / delta_time
opponent_speed_kph = opponent_speed_ms * 3.6

relative_speed = player.speed - opponent_speed_kph
```

**Output:** `float`, km/h (positive = player faster)
**Update:** Every frame, smoothed over 0.5s rolling window (15 frames)
**Dependencies:** None (base metric)

---

## 3. Closing Rate

Rate at which the gap between player and opponent is changing.

**Inputs:**
- Gap to Opponent (metric #1) at time `t` and `t-1`
- Frame timestamps

**Formula:**
```
closing_rate = (gap_meters[t-1] - gap_meters[t]) / delta_time
```

**Output:** `float`, meters/second (positive = closing, negative = falling back)
**Update:** Every frame, smoothed over 1.0s rolling window (30 frames)
**Dependencies:** Gap to Opponent (#1)

---

## 4. Slipstream Detection

Detect when player is within aerodynamic tow of an opponent.

**Inputs:**
- Gap to Opponent (#1)
- `player.world_pos_m.x/z` and `opponent.world_pos_m.x/z`
- `player.yaw` (heading)
- `player.speed`

**Formula:**
```
# Distance check
distance = sqrt((player.x - opponent.x)^2 + (player.z - opponent.z)^2)

# Alignment check: opponent must be roughly ahead on player's heading
dx = opponent.x - player.x
dz = opponent.z - player.z
angle_to_opponent = atan2(dx, dz)
heading_diff = abs(normalize_angle(angle_to_opponent - player.yaw))

slipstream_active = (
    distance < 30.0 and          # within 30 meters
    heading_diff < 0.26 and       # within ~15 degrees of heading
    player.speed > 200 and        # meaningful straight-line speed
    gap_meters > -35 and          # opponent ahead
    gap_meters < 0
)
```

**Output:** `bool`
**Update:** Every frame
**Dependencies:** Gap to Opponent (#1)

---

## 5. Attack Window Probability

Estimate probability that an overtake attempt is viable before the next braking zone.

**Inputs:**
- Gap to Opponent (#1)
- Closing Rate (#3)
- Distance to Next Corner (#6)
- Corner Severity (#7)
- Slipstream Detection (#4)
- `player.drsAllowed`, `player.drs`
- `player.ersStoreEnergy`

**Formula:**
```
# Time to reach opponent
if closing_rate > 0:
    time_to_close = abs(gap_meters) / closing_rate
else:
    time_to_close = float('inf')

# Time to reach next corner
time_to_corner = distance_to_next_corner / (player.speed / 3.6)

# Base probability from gap and closing rate
gap_factor = max(0, 1.0 - abs(gap_meters) / 30.0)       # closer = higher
close_factor = min(1.0, max(0, closing_rate / 5.0))       # faster closing = higher

# Modifiers
corner_factor = 1.0 if corner_severity == 'heavy' else 0.7 if corner_severity == 'medium' else 0.4
drs_bonus = 0.2 if player.drs or player.drsAllowed else 0.0
ers_bonus = 0.1 if player.ersStoreEnergy > 2_000_000 else 0.0
slipstream_bonus = 0.15 if slipstream_active else 0.0

# Can we reach them before the corner?
timing_ok = 1.0 if time_to_close < time_to_corner else 0.2

attack_window_probability = clamp(
    gap_factor * 0.3 +
    close_factor * 0.25 +
    corner_factor * 0.15 +
    timing_ok * 0.15 +
    drs_bonus + ers_bonus + slipstream_bonus,
    0.0, 1.0
)
```

**Output:** `float`, 0.0 to 1.0
**Update:** Every frame
**Dependencies:** Gap (#1), Closing Rate (#3), Slipstream (#4), Distance to Next Corner (#6), Corner Severity (#7)

---

## 6. Distance to Next Corner

Distance from player's current position to the next braking zone.

**Inputs:**
- `player.lapDistance`
- Track map `points[]` (precomputed curvature)
- `meta.track_length`

**Formula:**
```
# Precompute: identify braking zones from track map curvature
# For each point s, compute curvature:
curvature[s] = angle_change(s-5, s, s+5) / 10.0  # over 10m window

# Braking zone starts where curvature exceeds threshold
braking_zones = [s for s in range(track_length)
                 if curvature[s] > CURVATURE_THRESHOLD
                 and curvature[s-1] <= CURVATURE_THRESHOLD]

# Find next braking zone after player position
player_s = int(player.lapDistance) % track_length
next_corner_s = next(s for s in braking_zones if s > player_s)
# Handle wrap-around
if no match:
    next_corner_s = braking_zones[0] + track_length

distance_to_next_corner = next_corner_s - player_s
```

Where `angle_change(a, b, c)` computes the turn angle at point `b` given adjacent points from the track map `points[]`:
```
# Using map coordinates (u, v)
du1 = points[b].u - points[a].u
dv1 = points[b].v - points[a].v
du2 = points[c].u - points[b].u
dv2 = points[c].v - points[b].v
angle = atan2(du1*dv2 - dv1*du2, du1*du2 + dv1*dv2)
```

**Output:** `float`, meters (always positive, wraps around start/finish)
**Update:** Every frame (lookup from precomputed table)
**Dependencies:** Track map (precomputed at session start)

---

## 7. Corner Severity

Estimated corner difficulty based on curvature and typical speed.

**Inputs:**
- Track map `points[]` (precomputed)
- Curvature at corner apex

**Formula:**
```
# Precompute per braking zone:
# Find apex = point of maximum curvature within each corner
apex_curvature = max(curvature[s] for s in corner_range)

# Classify severity
if apex_curvature > 0.04:        # tight hairpin
    severity = 'heavy'            # heavy braking required
elif apex_curvature > 0.015:     # medium-speed corner
    severity = 'medium'
else:                             # fast kink
    severity = 'light'
```

**Output:** `enum: 'light' | 'medium' | 'heavy'`
**Update:** Precomputed once per track map (static lookup by lap distance)
**Dependencies:** Track map (precomputed at session start)

---

## 8. Braking Zone Entry Speed Delta

Speed difference between player and opponent when entering a braking zone.

**Inputs:**
- `player.speed` at braking zone entry
- Opponent speed (#2) at braking zone entry
- `player.brake` (to detect braking onset)
- Distance to Next Corner (#6)

**Formula:**
```
# Trigger: detect player entering braking zone
# (brake > 0.1 and within 150m of next corner start)
if player.brake > 0.1 and distance_to_next_corner < 150:
    if not in_braking_zone:
        in_braking_zone = True
        entry_speed_delta = player.speed - opponent_speed_kph
else:
    in_braking_zone = False

# Persist value until next braking zone
```

**Output:** `float`, km/h (positive = player entered faster, late-braking opportunity)
**Update:** Once per braking zone entry (event-triggered)
**Dependencies:** Relative Speed (#2), Distance to Next Corner (#6)

---

## 9. Lateral Track Position

Position of each car relative to the track centerline.

**Inputs:**
- `player.world_pos_m.x/z` (or opponent `world_pos_m.x/z`)
- Track map `points[]` — nearest centerline point
- Track normal vector at that point

**Formula:**
```
# Find nearest centerline point to car
car_pos = (world_pos_m.x, world_pos_m.z)
nearest_s = argmin(distance(car_pos, (points[s].u, points[s].v)))

# Compute track direction at nearest_s
tangent = (points[s+1].u - points[s].u, points[s+1].v - points[s].v)
normal = (-tangent[1], tangent[0])  # perpendicular (left-pointing)
normal = normalize(normal)

# Project car offset onto normal
offset_vec = (car_pos[0] - points[s].u, car_pos[1] - points[s].v)
lateral_offset = dot(offset_vec, normal)

# Normalize to approximate track half-width (~6 meters for F1)
TRACK_HALF_WIDTH = 6.0
lateral_position = clamp(lateral_offset / TRACK_HALF_WIDTH, -1.0, 1.0)
```

**Output:** `float`, -1.0 (left edge) to +1.0 (right edge), 0.0 = centerline
**Update:** Every frame
**Dependencies:** Track map

---

## 10. Overlap State

Detect how far alongside the opponent the player's car is.

**Inputs:**
- Gap to Opponent (#1) in meters
- `player.world_pos_m` and `opponent.world_pos_m`
- Lateral Track Position (#9) for both cars

**Formula:**
```
# Longitudinal gap (along track direction)
longitudinal_gap = abs(gap_meters)  # from metric #1

# Car length approximately 5.5m
CAR_LENGTH = 5.5

# Lateral separation
lateral_diff = abs(player_lateral - opponent_lateral)  # from metric #9
LATERAL_THRESHOLD = 0.3  # must be on different parts of track width

if longitudinal_gap > CAR_LENGTH * 1.5 or lateral_diff < LATERAL_THRESHOLD:
    overlap_state = 'none'
elif longitudinal_gap > CAR_LENGTH:
    overlap_state = 'front_wheel'      # noses overlapping
elif longitudinal_gap > CAR_LENGTH * 0.3:
    overlap_state = 'side_by_side'     # significant overlap
else:
    overlap_state = 'fully_alongside'  # cars level
```

**Output:** `enum: 'none' | 'front_wheel' | 'side_by_side' | 'fully_alongside'`
**Update:** Every frame
**Dependencies:** Gap to Opponent (#1), Lateral Track Position (#9)

---

## 11. Defensive Line Detection

Determine if the leading car moves toward the inside line to block.

**Inputs:**
- Opponent Lateral Track Position (#9), current and rolling history (1s)
- Distance to Next Corner (#6)
- Track map corner direction (left/right turn)

**Formula:**
```
# Determine which side is "inside" for next corner
next_corner_direction = sign(curvature[next_corner_apex])
# positive curvature = left turn, inside = left (negative lateral)
inside_side = -1.0 if next_corner_direction > 0 else +1.0

# Check if opponent is moving toward inside
opponent_lateral_now = opponent_lateral_position  # metric #9
opponent_lateral_1s_ago = rolling_buffer[-30]     # 30 frames = 1s

lateral_movement = opponent_lateral_now - opponent_lateral_1s_ago
moving_to_inside = (lateral_movement * inside_side) > 0

# Detection conditions
defensive_line = (
    distance_to_next_corner < 300 and     # approaching corner
    distance_to_next_corner > 50 and      # not yet in corner
    abs(lateral_movement) > 0.15 and      # meaningful lateral shift
    moving_to_inside and                   # moving toward inside
    abs(gap_meters) < 20                   # opponent is close ahead
)
```

**Output:** `bool`
**Update:** Every frame (uses 1s rolling window of lateral position)
**Dependencies:** Lateral Track Position (#9), Distance to Next Corner (#6), Corner Severity (#7)

---

## 12. Switchback Opportunity

Detect if the opponent compromises their exit speed due to a defensive entry line.

**Inputs:**
- Defensive Line Detection (#11) — was the opponent defensive?
- Exit Speed Delta (#13) — player faster on exit?
- Opponent Lateral Track Position (#9) — opponent on tight line?

**Formula:**
```
# Track state through corner phases
# Phase 1: Detect defensive entry (metric #11 was true on approach)
defensive_entry_detected = was_defensive_on_approach

# Phase 2: At corner exit (distance_to_next_corner wraps past 0)
if at_corner_exit:
    # Opponent took early/tight apex → poor exit
    opponent_tight_line = (opponent_lateral * inside_side) < -0.3

    # Player has better exit speed
    exit_speed_advantage = exit_speed_delta > 5.0  # km/h

    switchback_opportunity = (
        defensive_entry_detected and
        (opponent_tight_line or exit_speed_advantage)
    )
else:
    switchback_opportunity = False
```

**Output:** `bool`
**Update:** Event-triggered at corner exit
**Dependencies:** Defensive Line (#11), Exit Speed Delta (#13), Lateral Track Position (#9)

---

## 13. Exit Speed Delta

Difference in speed between cars exiting a corner.

**Inputs:**
- `player.speed`
- Opponent speed (from #2)
- `player.throttle` (detect full throttle = corner exit)
- Distance to Next Corner (#6) — detect transition from "in corner" to "exiting"

**Formula:**
```
# Detect corner exit: throttle goes above 0.9 after being below 0.5
if player.throttle > 0.9 and prev_throttle < 0.5:
    at_corner_exit = True
    exit_speed_player = player.speed
    exit_speed_opponent = opponent_speed_kph  # from metric #2
    exit_speed_delta = exit_speed_player - exit_speed_opponent

# Hold value until next corner exit event
```

**Output:** `float`, km/h (positive = player exited faster)
**Update:** Once per corner exit (event-triggered)
**Dependencies:** Relative Speed (#2)

---

## 14. Traction Limitation

Detect wheel slip or traction loss during acceleration.

**Inputs:**
- `player.throttle`
- `player.gForceLongitudinal`
- `player.speed`
- `player.tyreSurfaceTemp` (array [RL, RR, FL, FR])
- `player.tyreWear.*`

**Formula:**
```
# Expected acceleration given throttle input
# At full throttle, expect ~0.5-1.5G longitudinal
expected_accel = player.throttle * 1.0  # approximate baseline G

# Actual acceleration
actual_accel = player.gForceLongitudinal

# Traction loss: high throttle but low acceleration
traction_deficit = expected_accel - actual_accel

# Temperature factor: overheated rears lose grip
rear_temp_avg = (player.tyreSurfaceTemp[0] + player.tyreSurfaceTemp[1]) / 2
temp_risk = 1.0 if rear_temp_avg > 110 else 0.5 if rear_temp_avg > 100 else 0.0

# Wear factor
rear_wear_avg = (player.tyreWear.rearLeft + player.tyreWear.rearRight) / 2
wear_risk = 1.0 if rear_wear_avg > 60 else 0.5 if rear_wear_avg > 40 else 0.0

traction_limited = (
    player.throttle > 0.8 and
    traction_deficit > 0.3 and
    player.speed > 80  # not at standstill
)

traction_severity = clamp(traction_deficit + temp_risk * 0.2 + wear_risk * 0.2, 0.0, 1.0)
```

**Output:** `bool` (traction_limited) + `float` 0.0-1.0 (traction_severity)
**Update:** Every frame
**Dependencies:** None (base metric)

---

## 15. Risk Level

Estimate the risk level of an attack attempt.

**Inputs:**
- Gap to Opponent (#1)
- Overlap State (#10)
- Corner Severity (#7)
- Distance to Next Corner (#6)
- Closing Rate (#3)
- `player.tyreWear.*`
- `meta.weather`

**Formula:**
```
risk_score = 0.0

# Gap risk: tighter gap = higher risk
if abs(gap_meters) < 5:
    risk_score += 0.3
elif abs(gap_meters) < 15:
    risk_score += 0.15

# Overlap risk
if overlap_state == 'side_by_side':
    risk_score += 0.2
elif overlap_state == 'fully_alongside':
    risk_score += 0.3

# Corner risk
if corner_severity == 'heavy' and distance_to_next_corner < 100:
    risk_score += 0.3
elif corner_severity == 'medium' and distance_to_next_corner < 80:
    risk_score += 0.15

# Speed risk: high closing rate into braking zone
if closing_rate > 3.0 and distance_to_next_corner < 150:
    risk_score += 0.15

# Conditions risk
if meta.weather >= 3:  # rain
    risk_score += 0.1

rear_wear_avg = (player.tyreWear.rearLeft + player.tyreWear.rearRight) / 2
if rear_wear_avg > 50:
    risk_score += 0.1

risk_level = 'high' if risk_score > 0.6 else 'medium' if risk_score > 0.3 else 'low'
```

**Output:** `enum: 'low' | 'medium' | 'high'` + `float` 0.0-1.0 (risk_score)
**Update:** Every frame
**Dependencies:** Gap (#1), Closing Rate (#3), Distance to Next Corner (#6), Corner Severity (#7), Overlap State (#10)

---

## 16. Battle Intensity

Measure how aggressive/sustained the current battle is.

**Inputs:**
- Gap to Opponent (#1) — rolling 10s window
- Overlap State (#10) — rolling 10s window
- Closing Rate (#3) — rolling 10s window

**Formula:**
```
WINDOW = 300  # 10 seconds at 30 Hz

# Factor 1: How long gap has been small
close_frames = count(abs(gap_meters[t]) < 20 for t in window)
proximity_score = close_frames / WINDOW

# Factor 2: Number of overlap events
overlap_events = count_transitions(overlap_state, from='none', to=any_other, in=window)
overlap_score = min(1.0, overlap_events / 5.0)

# Factor 3: Closing rate oscillation (attacking back and forth)
sign_changes = count_sign_changes(closing_rate, in=window)
oscillation_score = min(1.0, sign_changes / 10.0)

battle_intensity = (
    proximity_score * 0.4 +
    overlap_score * 0.35 +
    oscillation_score * 0.25
)
```

**Output:** `float`, 0.0 to 1.0 (0 = no battle, 1 = intense wheel-to-wheel)
**Update:** Every frame (uses 10s rolling window)
**Dependencies:** Gap (#1), Closing Rate (#3), Overlap State (#10)

---

## 17. Overtake Attempt Detection

Detect when the player initiates an overtake move.

**Inputs:**
- Lateral Track Position (#9) — sudden lateral change
- Gap to Opponent (#1) — must be close
- `player.brake` — braking later than opponent
- Closing Rate (#3) — must be positive
- Overlap State (#10)

**Formula:**
```
# Lateral movement in last 0.5s (15 frames)
lateral_delta = abs(player_lateral[t] - player_lateral[t-15])

# Conditions for overtake attempt
overtake_attempt = (
    abs(gap_meters) < 15 and              # close to opponent
    closing_rate > 1.0 and                 # actively closing
    (
        lateral_delta > 0.3 or             # significant lateral move (pulling alongside)
        (overlap_state != 'none') or       # already overlapping
        (player.brake < opponent_brake      # braking later (late-brake move)
         and distance_to_next_corner < 100)
    )
)
```

**Output:** `bool`
**Update:** Every frame (uses 0.5s rolling window)
**Dependencies:** Gap (#1), Closing Rate (#3), Lateral Track Position (#9), Overlap State (#10)

---

## 18. Successful Overtake Detection

Detect when the player completes an overtake.

**Inputs:**
- `player.position` (current and previous frame)
- Target opponent `position` and `carIndex`
- Overtake Attempt Detection (#17) — was there an active attempt?

**Formula:**
```
# Track position changes for the target opponent
prev_player_pos = player.position[t-1]
curr_player_pos = player.position

# Simple detection: position improved
position_gained = prev_player_pos > curr_player_pos

# Confirmation: check specific opponent
# Find the opponent we were battling by carIndex
opponent = find_car(target_carIndex, in=nearbyCars or allCars)
opponent_behind_now = opponent.position > player.position

successful_overtake = (
    position_gained and
    opponent_behind_now and
    overtake_attempt_was_active  # within last 5 seconds
)
```

**Output:** `bool` (event)
**Update:** Every frame (event-triggered)
**Dependencies:** Overtake Attempt (#17)

---

## 19. Failed Overtake Detection

Detect when a player aborts an overtake attempt or drops back behind.

**Inputs:**
- Overtake Attempt Detection (#17) — was active
- Overlap State (#10) — went from overlap back to none
- Gap to Opponent (#1) — gap increasing again
- `player.position` — no improvement

**Formula:**
```
# An attempt was in progress
attempt_was_active = overtake_attempt_active_within(last_5_seconds)

# Player drops back
gap_increasing = closing_rate < -1.0  # falling back
overlap_lost = (
    prev_overlap_state != 'none' and
    overlap_state == 'none' and
    gap_meters < 0  # opponent still ahead
)

# No position gain
no_position_gain = player.position >= position_at_attempt_start

failed_overtake = (
    attempt_was_active and
    (overlap_lost or gap_increasing) and
    no_position_gain
)
```

**Output:** `bool` (event)
**Update:** Every frame (event-triggered)
**Dependencies:** Overtake Attempt (#17), Overlap State (#10), Gap (#1), Closing Rate (#3)

---

## 20. Defensive Success Detection

Detect when the defending car (player or opponent) successfully prevents a pass.

**Inputs:**
- Overtake Attempt Detection (#17) — opponent was attempting
- Failed Overtake Detection (#19) — attempt failed
- `player.position` — maintained

**Formula:**
```
# Detect opponent attacking us (we are defending)
opponent_attacking = (
    gap_meters > 0 and             # opponent behind us
    closing_rate < -1.0 and        # they are closing on us
    abs(gap_meters) < 15           # they are close
)

# Track if opponent overlaps us
opponent_overlapped = overlap_state != 'none'

# Defense succeeded if: opponent attacked, overlapped, then fell back
# without gaining a position
if opponent_attacking:
    defense_in_progress = True
    defense_start_position = player.position

if defense_in_progress and not opponent_attacking and abs(gap_meters) > 10:
    defense_in_progress = False
    defensive_success = (player.position <= defense_start_position)
```

**Output:** `bool` (event)
**Update:** Every frame (event-triggered, resolves over 5-10s)
**Dependencies:** Overtake Attempt (#17), Failed Overtake (#19), Gap (#1), Overlap State (#10)

---

# Metric Dependency Graph

```
Base (no dependencies):
  #2 Relative Speed
  #14 Traction Limitation

Track map (precomputed):
  #6 Distance to Next Corner
  #7 Corner Severity

Level 1 (from raw telemetry):
  #1 Gap to Opponent
  #9 Lateral Track Position

Level 2 (from level 1):
  #3 Closing Rate          ← #1
  #4 Slipstream Detection  ← #1
  #10 Overlap State        ← #1, #9
  #8 Braking Zone Entry    ← #2, #6
  #13 Exit Speed Delta     ← #2

Level 3 (from level 2):
  #5 Attack Window Prob    ← #1, #3, #4, #6, #7
  #11 Defensive Line       ← #6, #7, #9
  #15 Risk Level           ← #1, #3, #6, #7, #10
  #16 Battle Intensity     ← #1, #3, #10
  #17 Overtake Attempt     ← #1, #3, #9, #10

Level 4 (from level 3):
  #12 Switchback Opp       ← #9, #11, #13
  #18 Successful Overtake  ← #17
  #19 Failed Overtake      ← #1, #3, #10, #17

Level 5 (from level 4):
  #20 Defensive Success    ← #1, #10, #17, #19
```

---

# Implementation Notes

- All metrics should be computed in a single pass per frame, following the dependency order above (levels 0 → 5)
- Rolling window buffers should use fixed-size circular buffers (e.g., 300 frames = 10s at 30 Hz)
- Event-triggered metrics (#8, #12, #13, #18, #19, #20) should persist their last value until the next trigger
- Track map curvature and corner classification should be precomputed once when the track map is loaded
- Opponent identification: target the nearest car ahead from `nearbyCars[]` (smallest negative `gap`); fall back to `allCars[]` for `lapDistance`-based calculations
- These metrics form the **battle analysis layer** used by the racecraft AI
- They should be stored as structured telemetry features for AI model training
