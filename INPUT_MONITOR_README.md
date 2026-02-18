# Input Monitor - Testing Guide

## Issue You Just Encountered

**Problem:** No output when running `./test_inputs.sh`

**Root Cause:** Port 20777 was already in use by a previous receiver process.

**Fix:** Updated script now automatically kills any existing receiver before starting.

---

## Two Ways to Test

### 1. Test with Simulated Data (No Game Required)

```bash
./test_with_simulator.sh
```

- Uses mock F1 2025 packets
- Shows live input display at 10 Hz
- Good for verifying the monitor works
- **Note:** Steering won't change (simulated data has fixed values)

### 2. Test with Real F1 2025 Game

```bash
./test_inputs.sh
```

**Before running:**
1. Launch F1 2025
2. Go to: Settings → Telemetry Settings
3. Enable: **UDP Telemetry = ON**
4. Set: **UDP Port = 20777**
5. Join any session (Practice, Time Trial, Race)

**What you'll see:**
- Receiver starts and waits for packets
- Once you're in a session, live input monitor appears
- Shows at 10 Hz: steering, throttle, brake, gear, speed
- Turn your wheel to see steering move smoothly

---

## Steering Sign Convention

**Correct behavior:**
- Turn wheel **LEFT** → Negative values (e.g., -0.25)
- Turn wheel **RIGHT** → Positive values (e.g., +0.25)

**If inverted:**
Edit: `src/main/java/com/racingai/f1telemetry/state/CarState.java:110`
Change: `this.steer = -steer;`

---

## Troubleshooting

### "Address already in use" error
- Run: `pkill -f f1telemetry`
- Wait 2 seconds
- Try again

### No output after starting
1. Make sure F1 2025 is running and **in a session** (not in menus)
2. Verify UDP telemetry is enabled in game settings
3. Check port 20777 is not blocked by firewall

### Monitor shows but values don't change
- You need to actually drive in the game
- In menus, all inputs will be zero
- Join Practice or Time Trial to test

---

## What the Monitor Shows

```
Live Input Monitor - 10.0 Hz
================================================================================

Steer:    ░░░░░░░░░░░░░░░░░░░░|►►►░░░░░░░░░░░░░░░░░░ [+0.1234]
                                RIGHT

Throttle: ████████████████░░░░ [0.800]
Brake:    ░░░░░░░░░░░░░░░░░░░░ [0.000]

Gear:     7
Speed:    280 km/h
```

- **Steering bar:** Visual left/right indicator
- **Throttle/Brake:** 0.0 (off) to 1.0 (full)
- **Gear:** Current gear (0 = neutral, 1-8)
- **Speed:** km/h

Press **Ctrl+C** to stop
