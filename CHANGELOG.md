# Changelog

## Recent Fixes (2026-02-15)

### Fixed: Clean Ctrl+C Exit

**Problem:** Pressing Ctrl+C showed ugly Python traceback:
```
^CTraceback (most recent call last):
  File "/Users/physicxs/Documents/projects/racingAI/live_monitor.py", line 75, in <module>
    for line in sys.stdin:
KeyboardInterrupt
```

**Fixed:** All monitors now exit cleanly:
```
^C

✓ Monitor stopped
```

**Files updated:**
- [live_monitor.py](live_monitor.py) - Live dashboard monitor
- [monitor_inputs.py](monitor_inputs.py) - Simple input monitor

### Fixed: Nearby Cars Duplicate Display

**Problem:** Nearby cars showing duplicate entries:
```
║ NEARBY CARS                                                                    ║
║   P1  (behind): +0.00s                                                        ║
║   P1  (behind): +0.00s                                                        ║
║   P1  (behind): +0.00s                                                        ║
║   P1  (behind): +0.00s                                                        ║
║   P1  (behind): +0.00s                                                        ║
║   P1  (behind): +0.00s                                                        ║
```

**Root cause:** Test data (UDPPacketSender) was creating cars with same position and zero gap, which were being included as "nearby" cars.

**Fixed:** Added filtering to remove:
- Cars at the same position as player with 0 gap (duplicates/invalid)
- Cars with position 0 (uninitialized)

**Result:** Nearby cars section now only shows when there are actual valid nearby cars, or doesn't appear at all.

**Files updated:**
- [live_monitor.py](live_monitor.py) - Added validation filter for nearby cars

---

## Previous Major Features

### Track ID Support (2026-02-15)

**Added:**
- Track ID extraction from session packets
- Track name mapping (0-32 + -1 for unknown)
- [TrackIdMapper.java](src/main/java/com/racingai/f1telemetry/utils/TrackIdMapper.java) utility class
- Logging when session packets received with track name
- Session packet counting in statistics

**Fixed:** Initially misunderstood track ID 0 as "unknown" when it actually means "Melbourne (Australia)"

**Files:**
- [StateManager.java](src/main/java/com/racingai/f1telemetry/state/StateManager.java)
- [F1TelemetryApp.java](src/main/java/com/racingai/f1telemetry/F1TelemetryApp.java)
- [UDPPacketSender.java](src/main/java/com/racingai/f1telemetry/UDPPacketSender.java)
- [TrackIdMapper.java](src/main/java/com/racingai/f1telemetry/utils/TrackIdMapper.java)

### Live Monitor System (2026-02-15)

**Added:**
- Full dashboard monitor showing track, inputs, tyres, nearby cars
- Simple input-only monitor for steering verification
- Test modes with simulated data (no game required)
- Clean boxed UI with 10 Hz update rate

**Files:**
- [monitor.sh](monitor.sh), [monitor_test.sh](monitor_test.sh)
- [live_monitor.py](live_monitor.py)
- [test_inputs.sh](test_inputs.sh)
- [monitor_inputs.py](monitor_inputs.py)
- [MONITOR_GUIDE.md](MONITOR_GUIDE.md)
- [INPUT_MONITOR_README.md](INPUT_MONITOR_README.md)

### Recording System (2026-02-15)

**Added:**
- Record telemetry to JSONL files
- Auto-timestamped filenames
- Live recording statistics (duration, frame count, Hz)
- Recording summary on completion
- Test mode with simulated data

**Files:**
- [record.sh](record.sh), [record_test.sh](record_test.sh)
- [record_telemetry.py](record_telemetry.py)
- [RECORDING_GUIDE.md](RECORDING_GUIDE.md)

### Documentation (2026-02-15)

**Added:**
- [QUICK_START.md](QUICK_START.md) - Master getting started guide
- [MONITOR_GUIDE.md](MONITOR_GUIDE.md) - Complete monitor documentation
- [RECORDING_GUIDE.md](RECORDING_GUIDE.md) - Complete recording documentation
- [TRACK_ID_FIX.md](TRACK_ID_FIX.md) - Track ID explanation
- Updated [README.md](README.md) with quick start links

---

## Version History

### v1.1.0 - Monitoring & Recording (2026-02-15)
- Added live monitor system
- Added telemetry recording system
- Added track ID support
- Fixed nearby cars filtering
- Fixed Ctrl+C handling
- Comprehensive documentation

### v1.0.0 - Core System (Initial Release)
- UDP packet reception (port 20777)
- F1 2025 packet decoding
- State management
- JSON output at 30 Hz
- Nearby car selection
- 19 unit tests passing
