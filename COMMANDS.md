# F1 2025 Telemetry - Command Reference

All commands are run from the project root directory.

## Prerequisites

- Java 17+, Maven 3.6+
- Python 3 (for GUI and recording scripts)
- F1 2025 with UDP telemetry enabled (Settings > Telemetry > UDP Telemetry: ON, Port: 20777, Rate: 30 Hz)

## Live Monitoring

### Live Dashboard
Real-time terminal dashboard showing position, inputs, tyre wear, and nearby cars at 10 Hz.
```bash
./monitor.sh
```

### Input Monitor
Minimal monitor showing only steering, throttle, brake, gear, and speed.
```bash
./test_inputs.sh
```

## Recording

### Record a Session
Saves telemetry to a timestamped JSONL file (`telemetry_YYYYMMDD_HHMMSS.jsonl`). Press Ctrl+C to stop.
```bash
./record.sh
```

## Track Map

### Build a Track Map
Generates a 2D track map JSON from a recorded JSONL file. Needs at least one full lap of data.
The output file is auto-named `track_N_map.json` where N is the track ID (e.g. 0=Melbourne, 5=Monaco, 7=Silverstone).
```bash
./build_map.sh telemetry_20260315_105017.jsonl
# or with custom output name:
./build_map.sh telemetry_20260315_105017.jsonl monaco_map.json
```

### Live Track Map GUI
Shows your car moving on the track in real time with true track width rendering and a telemetry stats panel on the right (speed, tyres, DRS/ERS, G-force, damage, flags). Cars are positioned using world coordinates so you can see side-by-side battles, defensive lines, and off-track incidents.

Automatically records telemetry to a timestamped file and prints the replay command at startup.
```bash
./track_map_gui.sh track_N_map.json
```

**GUI Controls:**
| Key | Action |
|-----|--------|
| Scroll wheel | Zoom in/out (toward cursor) |
| Click + drag | Pan the map |
| `+` / `-` | Zoom in/out (center) |
| `R` | Reset zoom to fit |
| `F` | Follow player car (toggle) |

### Preview Track Map (No Game)
View a track map without live telemetry.
```bash
python3 track_map_live.py track_N_map.json --preview
```

## Race Replay

### Replay a Recorded Race
Plays back a recorded session on the track map with full telemetry stats panel.
```bash
./replay.sh track_N_map.json telemetry_YYYYMMDD_105017.jsonl
```

**Replay Controls:**
| Key | Action |
|-----|--------|
| `Space` | Play / pause |
| `Left` / `Right` | Skip -5s / +5s |
| `1` / `2` / `3` / `4` | Speed 1x / 2x / 4x / 0.5x |
| Click progress bar | Seek to position |
| Scroll / drag / `R` / `F` | Same as live map |

## Testing (No Game Required)

These scripts use a built-in UDP packet simulator so you can test without the F1 game.

### Test Live Monitor
```bash
./monitor_test.sh
```

### Test Input Monitor
```bash
./test_with_simulator.sh
```

### Test Recording (30 seconds)
```bash
./record_test.sh
```

### Test Track Map Builder
Records 60 seconds of simulated data, then builds a track map.
```bash
./build_map_test.sh
```

### Test Track Map GUI
Generates a test map if needed, then shows the GUI with a simulated moving car.
```bash
./track_map_gui_test.sh
```

## Building and Running Manually

```bash
# Compile
mvn clean compile

# Run tests
mvn test

# Run the telemetry receiver directly (outputs JSONL to stdout)
mvn -q exec:java -Dexec.mainClass="com.racingai.f1telemetry.F1TelemetryApp"

# Pipe to any Python tool
mvn -q exec:java -Dexec.mainClass="com.racingai.f1telemetry.F1TelemetryApp" 2>&1 | python3 live_monitor.py
mvn -q exec:java -Dexec.mainClass="com.racingai.f1telemetry.F1TelemetryApp" 2>&1 | python3 record_telemetry.py
mvn -q exec:java -Dexec.mainClass="com.racingai.f1telemetry.F1TelemetryApp" | python3 -u track_map_live.py track_5_map.json

# Run the UDP packet simulator (for testing without the game)
mvn -q exec:java -Dexec.mainClass="com.racingai.f1telemetry.UDPPacketSender"
```

## Typical Workflow

```
1. Start F1 2025, enable UDP telemetry
2. Record a race:           ./record.sh
3. Build track map:         ./build_map.sh telemetry_*.jsonl
4. Watch live with map:     ./track_map_gui.sh track_*_map.json
5. Replay after the race:   ./replay.sh track_*_map.json telemetry_*.jsonl
```

## Configuration

Edit `src/main/resources/application.properties`:

| Setting | Default | Description |
|---------|---------|-------------|
| `udp.port` | 20777 | UDP listening port |
| `output.rate.hz` | 30 | JSON output frame rate |
| `nearby.cars.max` | 6 | Max nearby cars in output |
| `nearby.cars.time.gap.seconds` | 1.5 | Time gap threshold (seconds) |
