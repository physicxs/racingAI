# Track ID Issue - Resolution

## What You Reported

Earlier you asked why I couldn't see the track was Australia when analyzing your telemetry. I had incorrectly stated that `track_id = 0` meant "unknown/not loaded".

## The Real Issue

**I was wrong!** The telemetry was actually **CORRECT** all along.

### F1 2025 Track ID Mapping

According to the F1 2025 UDP telemetry specification:
- **Track ID -1** = Unknown/Not Loaded
- **Track ID 0** = **Melbourne (Albert Park, Australia)** ✓
- Track ID 1 = Paul Ricard (France)
- Track ID 2 = Shanghai (China)
- ... and so on

Your race telemetry showed `track_id: 0` throughout all 14,245 frames, which was **correct** - you were racing at Melbourne/Australia!

## What Was Fixed

Even though the data was correct, there were issues with the codebase:

### 1. Missing Session Packet Tracking
**Problem:** Session packets weren't being counted in statistics
**Fixed:** Added session packet counter and logging in [F1TelemetryApp.java](src/main/java/com/racingai/f1telemetry/F1TelemetryApp.java)

### 2. Test Data Incomplete
**Problem:** `UDPPacketSender` (test packet generator) wasn't sending session packets
**Fixed:** Added `sendSessionPacket()` method that sends Melbourne/Australia track data

### 3. No Track Name Display
**Problem:** Raw track IDs are hard to interpret (what is track 0?)
**Fixed:** Created [TrackIdMapper.java](src/main/java/com/racingai/f1telemetry/utils/TrackIdMapper.java) with all track names

### 4. Better Logging
**Problem:** No visibility into when session packets are received
**Fixed:** Added logging in [StateManager.java](src/main/java/com/racingai/f1telemetry/state/StateManager.java) to show track name when session packets arrive

## How to Verify

Run the test packet sender and watch for session packet logs:

```bash
mvn -q exec:java -Dexec.mainClass="com.racingai.f1telemetry.UDPPacketSender"
```

In another terminal:
```bash
mvn -q exec:java -Dexec.mainClass="com.racingai.f1telemetry.F1TelemetryApp" 2>&1 | grep -i session
```

You should see:
```
Session packet received (total: 1)
Session packet received - Track: Melbourne (Australia) (ID: 0)
```

## Track ID Reference

For future reference, here are the main F1 tracks:

| ID | Track |
|----|-------|
| -1 | Unknown |
| **0** | **Melbourne (Australia)** |
| 1 | Paul Ricard (France) |
| 2 | Shanghai (China) |
| 3 | Sakhir (Bahrain) |
| 4 | Catalunya (Spain) |
| 5 | Monaco |
| 6 | Montreal (Canada) |
| 7 | Silverstone (Great Britain) |
| 10 | Spa (Belgium) |
| 11 | Monza (Italy) |
| 12 | Singapore |
| 13 | Suzuka (Japan) |
| 14 | Abu Dhabi (UAE) |
| 29 | Jeddah (Saudi Arabia) |
| 30 | Miami (USA) |
| 31 | Las Vegas (USA) |
| 32 | Losail (Qatar) |

See [TrackIdMapper.java](src/main/java/com/racingai/f1telemetry/utils/TrackIdMapper.java) for the complete list.

## Summary

✓ Your original telemetry was **correct**
✓ Track ID 0 = Australia (Melbourne/Albert Park)
✓ Codebase now has better session packet handling
✓ Track names are now displayed for clarity
