# Track Map Generation Guide

## Overview

Build accurate 2D track maps from recorded F1 2025 telemetry. The track map maps lap distance (meters) to 2D coordinates, enabling minimap rendering and car placement.

The builder uses world coordinates (X/Y/Z) from motion packets and lap distance from lap data to reconstruct the circuit geometry. No external track data is required.

## Prerequisites

- Telemetry system running (Java app on UDP port 20777)
- F1 2025 game with UDP telemetry enabled (30 Hz)

## Step 1: Record Telemetry

Start the recorder:

```bash
./record.sh
```

## Step 2: Drive Clean Laps

In F1 2025, enter **Time Trial** mode on the desired track.

Drive **3-5 clean laps**:

- Stay on track (avoid running wide or cutting corners)
- No flashbacks
- No pit lane entry
- Do not reset the session mid-recording

3 laps minimum, 5 laps recommended for better noise averaging.

## Step 3: Stop Recording

Press **Ctrl+C** to stop. Note the output filename (e.g., `telemetry_20260312_143000.jsonl`).

## Step 4: Build the Track Map

```bash
./build_map.sh telemetry_20260312_143000.jsonl
```

Or specify a custom output name:

```bash
./build_map.sh telemetry_20260312_143000.jsonl melbourne_map.json
```

## What the Builder Does

1. **Loads** all telemetry frames from the JSONL file
2. **Detects** which axis is height (smallest variance of X/Y/Z)
3. **Segments** data into complete laps (discards partial first/last laps)
4. **Resamples** each lap to 1-meter spacing via linear interpolation
5. **Averages** positions across all laps to reduce steering noise
6. **Closes** the loop so start and finish connect cleanly

## Validation Metrics

The builder prints:

- **Wrap-point gap** — distance between start and end points (should be < 5m after blending)
- **Mean lateral variance** — how much laps differ from each other (lower = more consistent driving)
- **Complete laps found** — how many full laps were usable

## Output Format

JSON file with structure:

```json
{
  "track_id": 0,
  "track_length_m": 5303,
  "coordinate_axes": {"u": "x", "v": "z"},
  "spacing_m": 1,
  "num_points": 5303,
  "points": [
    {"s": 0, "u": 100.5, "v": 200.3},
    {"s": 1, "u": 100.8, "v": 201.1}
  ]
}
```

Each point maps distance `s` (meters from start/finish) to 2D position `(u, v)`.

## Runtime Car Placement

To look up any car's map position at runtime given its `lapDistance`:

1. Clamp `s` to `[0, track_length)`
2. `i = floor(s)`, `t = s - i`
3. `(u, v) = points[i] + t * (points[i+1] - points[i])`

## Tips for Best Results

- **Time Trial mode** is ideal — no traffic, consistent racing line
- **More laps = better averaging** — 5 laps smooths out steering noise well
- **Avoid off-track excursions** — they create outlier positions that distort the map
- **One recording per track** — generate a separate map file for each circuit
