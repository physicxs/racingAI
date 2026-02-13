# Testing Guide - F1 2025 Telemetry Ingestion

This guide explains how to test the UDP telemetry receiver with both simulated packets and the actual F1 2025 game.

## Option 1: Test with Simulated Packets (No Game Required)

This is useful for testing the receiver and decoder without running the actual F1 2025 game.

### Step 1: Start the Telemetry Receiver

In one terminal window:

```bash
mvn exec:java -Dexec.mainClass="com.racingai.f1telemetry.F1TelemetryApp"
```

You should see:
```
F1 2025 Telemetry Ingestion System - Starting...
UDP Port: 20777
Output Rate: 30 Hz
UDP receiver started. Listening for F1 2025 telemetry on port 20777...
Press Ctrl+C to stop
```

### Step 2: Start the Packet Simulator

In another terminal window:

```bash
mvn exec:java -Dexec.mainClass="com.racingai.f1telemetry.UDPPacketSender"
```

You should see:
```
F1 2025 UDP Packet Sender (Test Tool)
Sending mock packets to localhost:20777
Press Ctrl+C to stop

Sent 100 packets (30.1 Hz)
Sent 200 packets (30.0 Hz)
...
```

### Step 3: Observe Received Packets

In the receiver window, you should now see:

```
First Motion packet received! Frame: 0, Session time: 0.00s
Lap Data - Position: 1, Lap: 5, Distance: 1500.0m, Speed trap: 320.5 km/h
Telemetry - Speed: 250 km/h, Gear: 7, Throttle: 80.0%, Brake: 0.0%
Packets: 100 total (Motion: 97, Lap: 10, Telemetry: 10, Damage: 0)
...
```

### Step 4: Stop Testing

Press **Ctrl+C** in each terminal to stop both the receiver and sender.

The receiver will display statistics:
```
=== Packet Statistics ===
Total packets: 1234
Motion packets: 1200
Lap data packets: 120
Telemetry packets: 120
Damage packets: 0
```

---

## Option 2: Test with Actual F1 2025 Game

### Prerequisites

1. **F1 2025 game** installed and running
2. **UDP Telemetry** enabled in game settings
3. Computer running the game must be able to send UDP to the receiver

### F1 2025 Game Configuration

1. Launch **F1 2025**
2. Go to **Settings** → **Telemetry Settings**
3. Configure as follows:
   - **UDP Telemetry:** **ON**
   - **UDP Broadcast Mode:** **ON** (if available)
   - **UDP IP Address:** `127.0.0.1` (for same machine) or your receiver's IP
   - **UDP Port:** **20777**
   - **UDP Send Rate:** **30 Hz**
   - **UDP Format:** **2025**

### Testing Steps

1. **Start the receiver:**
   ```bash
   mvn exec:java -Dexec.mainClass="com.racingai.f1telemetry.F1TelemetryApp"
   ```

2. **Start a session in F1 2025:**
   - Go to **Time Trial**, **Quick Race**, or any mode
   - Once on track, the receiver should start receiving packets

3. **What you should see:**
   ```
   First Motion packet received! Frame: 123, Session time: 4.06s
   Lap Data - Position: 12, Lap: 1, Distance: 234.5m, Speed trap: 0.0 km/h
   Telemetry - Speed: 245 km/h, Gear: 6, Throttle: 95.2%, Brake: 0.0%
   Damage - Tyre wear: FL=2.3%, FR=2.4%, RL=2.1%, RR=2.2%
   Packets: 100 total (Motion: 60, Lap: 1, Telemetry: 30, Damage: 9)
   ```

4. **Drive around the track** and observe live telemetry data

5. **Stop with Ctrl+C** to see final statistics

---

## Troubleshooting

### No Packets Received

**Problem:** Receiver starts but no packets appear

**Solutions:**
- **Firewall:** Check if port 20777/UDP is open
  ```bash
  # macOS/Linux - check if port is listening
  netstat -an | grep 20777
  ```
- **Game Settings:** Verify UDP telemetry is enabled in F1 2025
- **Network:** If running on different machines, check IP address configuration
- **Port conflict:** Make sure nothing else is using port 20777

### Decoder Errors

**Problem:** Packets received but "Error decoding packet" appears

**Solutions:**
- Check packet format version in game matches 2025
- Verify UDP format is set to "2025" not "2024" or earlier
- Check logs for specific error details

### Low Packet Rate

**Problem:** Receiving packets but much slower than 30 Hz

**Solutions:**
- Check F1 2025 "UDP Send Rate" setting (should be 30 Hz)
- Verify network isn't congested
- Check CPU usage on both game and receiver machines

---

## Expected Packet Types

When everything is working, you should see these packet types:

| Packet Type | Frequency | Contains |
|------------|-----------|----------|
| **Motion** | ~30 Hz | Car positions, velocities, G-forces |
| **Session** | ~1 Hz | Track info, weather, session metadata |
| **Lap Data** | ~1 Hz | Lap times, positions, gaps |
| **Telemetry** | ~30 Hz | Player inputs, speed, gear, RPM |
| **Car Status** | ~2 Hz | Fuel, ERS, DRS status |
| **Car Damage** | ~2 Hz | Tyre wear, component damage |

The receiver currently decodes: **Motion**, **Lap Data**, **Telemetry**, and **Damage** packets.

---

## Next Steps

Once you've verified the receiver works:

1. **Phase 5:** Implement state management to merge packet data
2. **Phase 6:** Add nearby cars selection logic
3. **Phase 7:** Generate JSON output stream at 30 Hz
4. **Phase 8:** Full integration testing
5. **Phase 9:** Performance validation with real racing data
