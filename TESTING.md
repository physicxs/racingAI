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
Configuration loaded:
  UDP Port: 20777
  Output Rate: 30 Hz
  Nearby Cars: max=6, timeGap=1.5s, ahead=4, behind=2
UDP receiver started on port 20777
JSON output started at 30 Hz
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

In the receiver window, you should now see JSON output streaming at 30 Hz:

```
{"timestamp":1771034117788,"sessionTime":0.5,"frameId":15,"player":{"position":1,"lapNumber":5,"lapDistance":1500.0,"speed":250,"gear":7,"throttle":0.8,"brake":0.0,"steering":0.0,"tyreWear":{"rearLeft":0.0,"rearRight":0.0,"frontLeft":0.0,"frontRight":0.0}},"nearbyCars":[]}
{"timestamp":1771034117821,"sessionTime":0.53,"frameId":16,"player":{"position":1,"lapNumber":5,"lapDistance":1510.5,"speed":252,"gear":7,"throttle":0.85,"brake":0.0,"steering":0.05,"tyreWear":{"rearLeft":0.0,"rearRight":0.0,"frontLeft":0.0,"frontRight":0.0}},"nearbyCars":[]}
...
```

Plus occasional logging messages:
```
First packet received - telemetry stream active
Packets: 1000 total (Motion: 970, Lap: 10, Telemetry: 10, Damage: 10)
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

#### Same Machine Setup

1. Launch **F1 2025**
2. Go to **Settings** → **Telemetry Settings**
3. Configure as follows:
   - **UDP Telemetry:** **ON**
   - **UDP Broadcast Mode:** **ON** (if available)
   - **UDP IP Address:** `127.0.0.1`
   - **UDP Port:** **20777**
   - **UDP Send Rate:** **30 Hz**
   - **UDP Format:** **2025**

#### Cross-Machine Setup (Different Computers)

If F1 2025 is on a different machine than the receiver:

1. **Find receiver's IP address:**
   ```bash
   # On Mac/Linux receiver
   ifconfig | grep "inet " | grep -v 127.0.0.1
   # Look for IP like 192.168.1.116

   # On Windows receiver
   ipconfig
   # Look for IPv4 Address under your active network adapter
   ```

2. **Configure F1 2025 on Windows:**
   - **UDP Telemetry:** **ON**
   - **UDP Broadcast Mode:** **OFF**
   - **UDP IP Address:** `192.168.1.116` (your receiver's IP)
   - **UDP Port:** **20777**
   - **UDP Send Rate:** **30 Hz**
   - **UDP Format:** **2025**

3. **Verify network connectivity from Windows:**
   ```cmd
   ping 192.168.1.116
   ```
   You should see replies. If not, check firewall settings.

4. **Allow firewall on receiver machine** (if needed):
   ```bash
   # Mac: Allow Java to receive UDP
   sudo /usr/libexec/ApplicationFirewall/socketfilterfw --add /usr/bin/java
   ```

### Testing Steps

1. **Start the receiver:**
   ```bash
   mvn exec:java -Dexec.mainClass="com.racingai.f1telemetry.F1TelemetryApp"
   ```

2. **Start a session in F1 2025:**
   - Go to **Time Trial**, **Quick Race**, or any mode
   - Once on track, the receiver should start receiving packets

3. **What you should see:**

   Streaming JSON output at 30 Hz:
   ```json
   {"timestamp":1771034117788,"sessionTime":421.569,"frameId":17647,"player":{"position":9,"lapNumber":5,"lapDistance":1.4140625,"speed":304,"gear":8,"throttle":1.0,"brake":0.0,"steering":8.20861E-4,"tyreWear":{"rearLeft":13.52763,"rearRight":9.815713,"frontLeft":13.483042,"frontRight":5.848298}},"nearbyCars":[{"carIndex":0,"position":10,"gap":0.228},{"carIndex":7,"position":11,"gap":0.662},{"carIndex":8,"position":12,"gap":1.145}]}
   ```

   Plus logging messages:
   ```
   First packet received - telemetry stream active
   Packets: 1000 total (Motion: 600, Lap: 30, Telemetry: 300, Damage: 70)
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

## JSON Output Format

The system outputs newline-delimited JSON (JSONL) at 30 Hz. Each line contains:

- **timestamp**: Unix timestamp in milliseconds
- **sessionTime**: Game session time in seconds
- **frameId**: Game frame identifier
- **player**: Player car telemetry
  - position, lapNumber, lapDistance
  - speed, gear, throttle, brake, steering
  - tyreWear (all four tyres)
- **nearbyCars**: Array of nearby cars (up to 6 within 1.5s gap)
  - carIndex, position, gap (in seconds)

You can redirect the JSON output to a file:
```bash
mvn exec:java -Dexec.mainClass="com.racingai.f1telemetry.F1TelemetryApp" > telemetry.jsonl
```

The logging goes to stderr, so it won't interfere with the JSON output to stdout.
