# System Validation Guide

This document provides validation procedures for the F1 2025 Telemetry Ingestion System.

## Phase 9: Testing and Validation

### Objective

Validate that the complete system works correctly end-to-end with actual F1 2025 game data.

---

## Validation Checklist

### 1. Unit Tests

All unit tests must pass:

```bash
mvn test
```

**Expected Result:**
- 19+ tests pass
- 0 failures
- 0 errors (except expected port-in-use error if receiver is running)

**Validation Criteria:**
- ✅ JsonOutputGeneratorTest: 3 tests
- ✅ StateManagerTest: 5 tests
- ✅ NearbyCarsSelectorTest: 7 tests
- ✅ PacketDecoderTest: 4 tests

---

### 2. Configuration Loading

Verify configuration is loaded correctly:

```bash
mvn exec:java -Dexec.mainClass="com.racingai.f1telemetry.F1TelemetryApp"
```

**Expected Output:**
```
F1 2025 Telemetry Ingestion System - Starting...
Configuration loaded:
  UDP Port: 20777
  Output Rate: 30 Hz
  Nearby Cars: max=6, timeGap=1.5s, ahead=4, behind=2
```

**Validation Criteria:**
- ✅ Configuration loaded from application.properties
- ✅ All values match configuration file
- ✅ No errors or warnings about missing configuration

---

### 3. UDP Packet Reception

**Test with Simulated Packets:**

Terminal 1:
```bash
mvn exec:java -Dexec.mainClass="com.racingai.f1telemetry.F1TelemetryApp"
```

Terminal 2:
```bash
mvn exec:java -Dexec.mainClass="com.racingai.f1telemetry.UDPPacketSender"
```

**Validation Criteria:**
- ✅ Receiver binds to port 20777
- ✅ First packet received message appears
- ✅ Packet count increases every 1000 packets
- ✅ No decoder errors or exceptions

---

### 4. JSON Output Stream

**Test JSON Output Quality:**

```bash
mvn exec:java -Dexec.mainClass="com.racingai.f1telemetry.F1TelemetryApp" 2>/dev/null | head -5 | jq .
```

**Expected Output:**
```json
{
  "timestamp": 1771034117788,
  "sessionTime": 421.569,
  "frameId": 17647,
  "player": {
    "position": 9,
    "lapNumber": 5,
    "lapDistance": 1.4140625,
    "speed": 304,
    "gear": 8,
    "throttle": 1.0,
    "brake": 0.0,
    "steering": 0.000820861,
    "tyreWear": {
      "rearLeft": 13.52763,
      "rearRight": 9.815713,
      "frontLeft": 13.483042,
      "frontRight": 5.848298
    }
  },
  "nearbyCars": [
    {
      "carIndex": 0,
      "position": 10,
      "gap": 0.228
    }
  ]
}
```

**Validation Criteria:**
- ✅ Valid JSON (parseable by `jq`)
- ✅ All required fields present
- ✅ Output rate ~30 Hz (33ms between lines)
- ✅ Realistic telemetry values

---

### 5. State Management

**Test State Updates:**

Run with actual F1 2025 game and observe player state changes:

**Validation Criteria:**
- ✅ Speed updates reflect game speed
- ✅ Gear changes correctly (1-8)
- ✅ Throttle/brake values range 0.0-1.0
- ✅ Position updates during race
- ✅ Lap number increments at finish line
- ✅ Tyre wear increases over laps

---

### 6. Nearby Cars Selection

**Test with Multiple AI Cars:**

Start a race with AI opponents and observe `nearbyCars` array:

**Validation Criteria:**
- ✅ Up to 6 cars maximum
- ✅ Only cars within 1.5s gap
- ✅ Cars ahead have negative gap
- ✅ Cars behind have positive gap
- ✅ Gap values realistic (-1.5s to +1.5s)
- ✅ Array empty when isolated

**Example Output:**
```json
"nearbyCars": [
  {"carIndex": 5, "position": 7, "gap": -0.8},
  {"carIndex": 0, "position": 9, "gap": 0.2},
  {"carIndex": 7, "position": 10, "gap": 0.6}
]
```

---

### 7. Performance Validation

**Test Output Rate:**

```bash
mvn exec:java -Dexec.mainClass="com.racingai.f1telemetry.F1TelemetryApp" 2>/dev/null | \
  pv -l -a > /dev/null
```

**Expected Result:**
```
[ 30.0 lines/s ]
```

**Validation Criteria:**
- ✅ Output rate: 28-32 Hz (target: 30 Hz)
- ✅ Stable rate (no significant drops)
- ✅ Low CPU usage (<10% on modern hardware)
- ✅ Low memory usage (<200MB)

---

### 8. Cross-Machine Testing

**Test Network Reception:**

F1 2025 on Windows → Receiver on Mac/Linux

**Validation Criteria:**
- ✅ Packets received across network
- ✅ No packet loss (continuous frame IDs)
- ✅ Latency <10ms
- ✅ Firewall allows UDP/20777

---

### 9. Long-Duration Testing

**Test Stability:**

Run a full F1 race (20+ laps, 30+ minutes):

**Validation Criteria:**
- ✅ No memory leaks (memory stable)
- ✅ No packet loss over time
- ✅ Output rate remains 30 Hz
- ✅ No crashes or exceptions
- ✅ Graceful shutdown with Ctrl+C

---

### 10. Error Handling

**Test Error Scenarios:**

1. **Port Already in Use:**
   ```bash
   # Start receiver twice
   mvn exec:java -Dexec.mainClass="com.racingai.f1telemetry.F1TelemetryApp"
   mvn exec:java -Dexec.mainClass="com.racingai.f1telemetry.F1TelemetryApp"
   ```
   - ✅ Second instance fails with clear error message

2. **Invalid Packets:**
   - Handled gracefully by decoder
   - ✅ Warnings logged, not crashes

3. **Player Not Active:**
   - In menus, garage, or spectating
   - ✅ No JSON output (null check)

---

## Success Criteria

All validation points must pass:

- ✅ All unit tests pass
- ✅ Configuration loads correctly
- ✅ UDP packets received from game
- ✅ JSON output valid and 30 Hz
- ✅ State updates reflect game state
- ✅ Nearby cars selected correctly
- ✅ Performance targets met
- ✅ Stable over long sessions
- ✅ Error handling works

---

## Known Limitations

1. **Session Detection**: System doesn't detect session end, continues outputting last state
2. **Packet Loss**: No detection or reporting of dropped UDP packets
3. **Time Synchronization**: Uses system time, not synchronized with game time
4. **Format Support**: Only F1 2025 UDP format (not backwards compatible)

---

## Next Steps After Validation

Once all validation passes:

1. Package for distribution: `mvn package`
2. Document deployment procedures
3. Consider integration with external systems
4. Potential future enhancements:
   - Session start/end detection
   - Packet loss monitoring
   - Historical data recording
   - Real-time analytics dashboard
