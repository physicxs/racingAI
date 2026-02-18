# Live Telemetry Monitor Guide

## Overview

Comprehensive live monitor showing all F1 2025 telemetry data at 10 Hz in a clean dashboard format.

## What It Shows

```
╔════════════════════════════════════════════════════════════════════════════════╗
║ F1 2025 LIVE TELEMETRY MONITOR                                                 ║
║ 10.0 Hz                                                                        ║
╠════════════════════════════════════════════════════════════════════════════════╣
║ TRACK: Melbourne (Australia)                                                  ║
║ Position: P4  │  Lap: 5  │  Distance: 3809.2m                                 ║
╠════════════════════════════════════════════════════════════════════════════════╣
║ INPUTS                                                                         ║
║   Steer:    ░░░░░░░░░░░░░░░░░░░░|►►►░░░░░░░░░░░░░░░░░░ [+0.024] RIGHT        ║
║   Throttle: ████████████████████ [1.000]                                      ║
║   Brake:    ░░░░░░░░░░░░░░░░░░░░ [0.000]                                      ║
║                                                                                ║
║   Gear: 7   │  Speed: 280 km/h                                                ║
╠════════════════════════════════════════════════════════════════════════════════╣
║ TYRE WEAR                                                                      ║
║   FL: 12.8%  │  FR:  5.4%                                                     ║
║   RL: 10.0%  │  RR:  8.0%                                                     ║
╠════════════════════════════════════════════════════════════════════════════════╣
║ NEARBY CARS                                                                    ║
║   P5 (behind): +0.25s                                                          ║
╚════════════════════════════════════════════════════════════════════════════════╝
```

## Features

- **Track Information**: Shows track name and ID
- **Position & Lap**: Current position, lap number, lap distance
- **Steering**: Visual bar showing left/right with numeric value
- **Throttle/Brake**: Visual bars with percentages
- **Gear & Speed**: Current gear and speed in km/h
- **Tyre Wear**: All 4 tyres (FL, FR, RL, RR)
- **Nearby Cars**: Up to 6 cars within 1.5s, showing gap

## How to Use

### Option 1: Test with Simulated Data

```bash
./monitor_test.sh
```

Perfect for testing without the game. Shows Melbourne track with simulated telemetry.

### Option 2: Live with F1 2025

```bash
./monitor.sh
```

**Before running:**
1. Launch F1 2025
2. Enable UDP telemetry: Settings → Telemetry Settings → UDP: ON
3. Set port to 20777
4. Join any session (Practice, Time Trial, Race)

### Option 3: Simple Input Monitor

For just steering/throttle/brake without the full dashboard:

```bash
./test_inputs.sh
```

## Stopping the Monitor

Press **Ctrl+C** to stop

## Files

- [monitor.sh](monitor.sh) - Main live monitor (requires F1 2025)
- [monitor_test.sh](monitor_test.sh) - Test with simulated data
- [live_monitor.py](live_monitor.py) - Python monitor script
- [test_inputs.sh](test_inputs.sh) - Simple input-only monitor

## Troubleshooting

### No data appearing
1. Make sure F1 2025 is **in a session** (not in menus)
2. Verify UDP telemetry is enabled in game settings
3. Check port 20777 is not blocked

### "Address already in use" error
```bash
pkill -f f1telemetry
sleep 2
./monitor.sh
```

### Monitor shows but values stuck at zero
You're in the menus. Join a Practice or Time Trial session and start driving.

## Track IDs

The monitor automatically shows track names:

| ID | Track Name |
|----|-----------|
| 0 | Melbourne (Australia) |
| 3 | Sakhir (Bahrain) |
| 5 | Monaco |
| 7 | Silverstone (Great Britain) |
| 10 | Spa (Belgium) |
| 11 | Monza (Italy) |
| 12 | Singapore |
| 13 | Suzuka (Japan) |
| 29 | Jeddah (Saudi Arabia) |
| 30 | Miami (USA) |
| 31 | Las Vegas (USA) |

See [TrackIdMapper.java](src/main/java/com/racingai/f1telemetry/utils/TrackIdMapper.java) for complete list.

## Comparison: Monitors Available

| Monitor | Shows | Use Case |
|---------|-------|----------|
| **monitor.sh** | Full dashboard (track, inputs, tyres, nearby cars) | Main monitor for driving |
| **test_inputs.sh** | Just inputs (steering, throttle, brake, gear, speed) | Quick steering verification |
| **monitor_test.sh** | Full dashboard with simulated data | Testing without game |

All monitors update at 10 Hz for smooth real-time display.
