# Telemetry Recording Guide

## Overview

Record F1 2025 telemetry sessions to JSONL files for later analysis. Shows live statistics while recording.

## Quick Start

### Test Recording (No Game Required)

```bash
./record_test.sh
```

Records 30 seconds of simulated data to verify everything works.

### Live Recording with F1 2025

```bash
./record.sh
```

**Before running:**
1. Launch F1 2025
2. Enable UDP telemetry in settings (port 20777)
3. Join a session
4. Run the script
5. Start driving
6. Press **Ctrl+C** when done

## What You'll See While Recording

```
╔════════════════════════════════════════════════════════════════════════════════╗
║ F1 2025 TELEMETRY RECORDER                                                     ║
╚════════════════════════════════════════════════════════════════════════════════╝

Recording to: telemetry_20260215_143022.jsonl

Waiting for telemetry data...

✓ Recording started!

Recording: 02:45 │ Frames: 4,950 │ Rate: 30.0 Hz
Track: Melbourne │ P4 │ Lap 5 │ 280 km/h
```

**Live stats update every second:**
- Duration (MM:SS)
- Frame count
- Recording rate (Hz)
- Current track, position, lap, speed

## After Recording

When you press Ctrl+C, you'll see a summary:

```
================================================================================
RECORDING COMPLETE
================================================================================
File:           telemetry_20260215_143022.jsonl
Duration:       05:23
Frames:         9,690
Average rate:   30.0 Hz
Track:          Melbourne
Final position: P4
Laps recorded:  5
================================================================================
```

## File Format

Recordings are saved as **JSONL** (JSON Lines):
- One JSON object per line
- Each line is a complete telemetry snapshot
- File name: `telemetry_YYYYMMDD_HHMMSS.jsonl`

**Example line:**
```json
{"timestamp":1771192828913,"sessionTime":396.48,"frameId":16270,"meta":{"track_id":0},"player":{"position":4,"lapNumber":5,"lapDistance":3809.2,"speed":280,"gear":7,"throttle":1.0,"brake":0.0,"steering":0.024,"tyreWear":{"rearLeft":9.97,"rearRight":8.00,"frontLeft":12.81,"frontRight":5.40}},"nearbyCars":[{"carIndex":5,"position":5,"gap":0.25,"world_pos_m":{"x":635.63,"y":4.01,"z":461.39}}]}
```

## Analyzing Recorded Data

You can analyze recordings with Python:

```python
import json

# Read the file
with open('telemetry_20260215_143022.jsonl', 'r') as f:
    for line in f:
        data = json.loads(line)

        # Access telemetry data
        track_id = data['meta']['track_id']
        position = data['player']['position']
        speed = data['player']['speed']
        steering = data['player']['steering']

        # Your analysis here
        print(f"Frame {data['frameId']}: P{position} at {speed} km/h")
```

**Example analyses:**
- Extract all steering inputs
- Calculate average speed per lap
- Analyze tyre wear progression
- Find position changes
- Compare throttle/brake patterns
- Identify fastest sectors

## Use Cases

### 1. Race Analysis
Record a full race and analyze:
- Where you gained/lost positions
- Lap time consistency
- Tyre degradation patterns
- Fuel strategy impact

### 2. Track Learning
Record practice sessions to:
- Compare corner speeds
- Analyze racing line (via steering)
- Find braking points
- Optimize gear shifts

### 3. Setup Testing
Record multiple runs with different setups:
- Compare lap times
- Analyze tyre wear rates
- Study handling balance (steering inputs)
- Evaluate top speeds

### 4. Training Data
Collect telemetry for machine learning:
- Driver behavior patterns
- Optimal racing lines
- Adaptive difficulty tuning
- Performance prediction

## Files Created

Each recording creates one JSONL file:
```
telemetry_20260215_143022.jsonl    # Your recording
telemetry_20260215_150845.jsonl    # Another session
```

**File naming:**
- `telemetry_` prefix
- Date: YYYYMMDD
- Time: HHMMSS
- `.jsonl` extension

## Comparison: Available Tools

| Tool | Purpose | Output |
|------|---------|--------|
| **record.sh** | Record telemetry to file | JSONL file + stats |
| **monitor.sh** | Live dashboard display | Screen only |
| **test_inputs.sh** | Test steering/inputs | Screen only |

You can record and monitor simultaneously by running both in separate terminals!

## Tips

### Recording Multiple Sessions
Each run creates a new timestamped file, so you can safely record multiple sessions without overwriting.

### File Size
At 30 Hz, expect:
- ~1 KB per second
- ~60 KB per minute
- ~3.6 MB per hour

A typical 5-lap session (~10 minutes) = ~600 KB

### Storage Location
Files are saved in the project root directory. Move them to a separate folder if you record many sessions:

```bash
mkdir recordings
mv telemetry_*.jsonl recordings/
```

### Stopping Recording
Always use **Ctrl+C** to stop cleanly. This ensures:
- File is properly closed
- Summary statistics are displayed
- Last frames are written

## Troubleshooting

### No frames being recorded
1. Check F1 2025 is running and in a session
2. Verify UDP telemetry is enabled
3. Make sure you're driving (not in menus)

### Recording rate too low
- Close other applications
- Check CPU usage
- Ensure F1 2025 is sending at 30 Hz (check game settings)

### File not found after recording
Files are saved in the project root. Check:
```bash
ls -lt telemetry_*.jsonl | head
```

### Want to record to a specific filename
Edit [record_telemetry.py:16](record_telemetry.py#L16):
```python
filename = "my_session.jsonl"  # Instead of auto-generated name
```

## Scripts

- [record.sh](record.sh) - Main recorder (requires F1 2025)
- [record_test.sh](record_test.sh) - Test with simulated data
- [record_telemetry.py](record_telemetry.py) - Python recorder script
