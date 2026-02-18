# F1 2025 Telemetry System - Quick Start

## What You Have

Three modes of operation:

1. **🎮 Live Monitor** - Real-time dashboard while driving
2. **📊 Input Testing** - Verify steering/controls work
3. **💾 Recording** - Save telemetry to files for analysis

---

## 🎮 Live Monitor

Shows everything in real-time: track, position, inputs, tyres, nearby cars.

```bash
./monitor.sh
```

Perfect for: Practicing, racing, real-time feedback

**Test without game:**
```bash
./monitor_test.sh
```

See: [MONITOR_GUIDE.md](MONITOR_GUIDE.md)

---

## 📊 Input Testing

Simple display showing just your inputs (steering, throttle, brake, gear, speed).

```bash
./test_inputs.sh
```

Perfect for: Verifying steering works, calibrating controls

See: [INPUT_MONITOR_README.md](INPUT_MONITOR_README.md)

---

## 💾 Recording

Record telemetry to JSONL files for later analysis.

```bash
./record.sh
```

Perfect for: Race analysis, data collection, performance review

**Test without game:**
```bash
./record_test.sh
```

Creates files like: `telemetry_20260215_143022.jsonl`

See: [RECORDING_GUIDE.md](RECORDING_GUIDE.md)

---

## Setup (First Time Only)

### 1. F1 2025 Settings

In-game settings:
- Go to: **Settings → Telemetry Settings**
- Set: **UDP Telemetry = ON**
- Set: **UDP Port = 20777**

### 2. Test the System

Without the game:
```bash
./monitor_test.sh
```

You should see a live dashboard with simulated data.

Press Ctrl+C to stop.

### 3. Try With F1 2025

1. Start F1 2025
2. Join any session (Practice, Time Trial, Race)
3. In another terminal:
   ```bash
   ./monitor.sh
   ```
4. Start driving
5. See live telemetry!

---

## Common Workflows

### Practice Session with Live Feedback
```bash
./monitor.sh
```
Watch your inputs, tyre wear, and position in real-time.

### Record a Race for Analysis
```bash
./record.sh
```
Drive your race, press Ctrl+C when done. Analyze the JSONL file later.

### Both at the Same Time
Terminal 1:
```bash
./monitor.sh
```

Terminal 2:
```bash
./record.sh
```

Get live feedback AND save data for later!

### Check Steering Works
```bash
./test_inputs.sh
```
Turn your wheel and verify steering shows negative (left) and positive (right).

---

## What Each Script Does

| Script | Display | Saves Data | Use Case |
|--------|---------|------------|----------|
| `monitor.sh` | ✓ Full dashboard | ✗ | Live driving feedback |
| `monitor_test.sh` | ✓ Full dashboard | ✗ | Test without game |
| `test_inputs.sh` | ✓ Inputs only | ✗ | Verify controls |
| `record.sh` | ✓ Stats only | ✓ JSONL | Data collection |
| `record_test.sh` | ✓ Stats only | ✓ JSONL | Test recording |

---

## Troubleshooting

### No output appears
- Make sure F1 2025 is **in a session** (not menus)
- Check UDP telemetry is enabled in game
- Verify port 20777 is not blocked

### "Address already in use"
```bash
pkill -f f1telemetry
sleep 2
# Then try again
```

### Values stuck at zero
You're in the menus. Join a session and start driving.

### Steering inverted?
If left = positive and right = negative, flip the sign at:
- [CarState.java:110](src/main/java/com/racingai/f1telemetry/state/CarState.java#L110)
- Change: `this.steer = -steer;`

---

## File Locations

```
racingAI/
├── monitor.sh              # Live monitor (F1 2025)
├── monitor_test.sh         # Live monitor (simulated)
├── test_inputs.sh          # Input testing
├── record.sh               # Record telemetry (F1 2025)
├── record_test.sh          # Record telemetry (simulated)
├── live_monitor.py         # Monitor script
├── record_telemetry.py     # Recorder script
├── telemetry_*.jsonl       # Your recordings (auto-generated)
├── MONITOR_GUIDE.md        # Monitor documentation
├── RECORDING_GUIDE.md      # Recording documentation
└── QUICK_START.md          # This file
```

---

## Next Steps

1. **Test everything works:**
   ```bash
   ./monitor_test.sh
   ```

2. **Try with F1 2025:**
   ```bash
   ./monitor.sh
   ```

3. **Record your first session:**
   ```bash
   ./record.sh
   ```

4. **Analyze your data:**
   See [RECORDING_GUIDE.md](RECORDING_GUIDE.md) for Python examples

---

## Support

- Full monitor guide: [MONITOR_GUIDE.md](MONITOR_GUIDE.md)
- Recording guide: [RECORDING_GUIDE.md](RECORDING_GUIDE.md)
- Input testing: [INPUT_MONITOR_README.md](INPUT_MONITOR_README.md)
- Track ID info: [TRACK_ID_FIX.md](TRACK_ID_FIX.md)

**All scripts are ready to run - just launch F1 2025 and go!**
