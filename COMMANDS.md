# F1 2025 Telemetry - Command Reference

All commands are run from the project root directory.

## Prerequisites

- Java 17+, Maven 3.6+
- Python 3 (for GUI and recording scripts)
- F1 2025 with UDP telemetry enabled (Settings > Telemetry > UDP Telemetry: ON, Port: 20777, Rate: 30 Hz)

## How to Build a Track Map

### Step 1: Record telemetry
Start a race or time trial in F1 2025, then run:
```bash
./record.sh
```
Drive 3-5 laps varying your line (some laps left, some right, some normal). Press **Ctrl+C** to stop. This saves a timestamped file in the `telemetry/` folder like `telemetry/telemetry_20260317_133507.jsonl`.

To cancel without saving, press Ctrl+C then delete the file:
```bash
rm telemetry/telemetry_20260317_133507.jsonl
```

### Step 2: Build the track map
```bash
./build_true_centerline.sh telemetry/telemetry_20260317_133507.jsonl
```
This outputs to `Track Map Builds/track_N_true_map.json` (e.g. `Track Map Builds/track_0_true_map.json` for Melbourne).

To combine multiple recordings:
```bash
./build_true_centerline.sh telemetry/left_laps.jsonl telemetry/right_laps.jsonl telemetry/normal.jsonl
```

### Step 3: Build track intelligence (optional)
```bash
./build_intelligence.sh "Track Map Builds/track_0_true_map.json"
```
This outputs `Track Map Builds/track_0_intelligence.json` with per-point curvature, corner detection, corner phases (entry/apex/exit), and target speed.

### Step 4: Analyze driver performance (optional)
```bash
./analyze_driver.sh "Track Map Builds/track_0_intelligence.json" telemetry/telemetry_20260317_161505.jsonl
```
This outputs `Track Map Builds/track_0_driver_analysis.json` with per-corner scores (entry/apex/exit), speed deltas, and lateral error.

### Step 5: Use the track map
Watch live with the GUI (also auto-records telemetry for replay):
```bash
./track_map_gui.sh "Track Map Builds/track_0_true_map.json"
```

Or replay a previous session:
```bash
./replay.sh "Track Map Builds/track_0_true_map.json" telemetry/telemetry_20260317_133507.jsonl
```

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

## Track Map GUI

Shows your car moving on the track in real time with true track width rendering and a telemetry stats panel (speed, tyres, DRS/ERS, G-force, damage, flags). Cars are positioned using world coordinates so you can see side-by-side battles, defensive lines, and off-track incidents.

**Controls:**
| Key | Action |
|-----|--------|
| Scroll wheel | Zoom in/out (toward cursor) |
| Click + drag | Pan the map |
| `+` / `-` | Zoom in/out (center) |
| `R` | Reset zoom to fit |
| `F` | Follow player car (toggle) |

### Preview Track Map (No Game)
```bash
python3 track_map_live.py "Track Map Builds/track_0_true_map.json" --preview
```

### Debug Car Positioning
Print lateral offsets per car to stderr:
```bash
./track_map_gui.sh "Track Map Builds/track_0_true_map.json" --debug
./replay.sh "Track Map Builds/track_0_true_map.json" telemetry.jsonl --debug
```

## Race Replay

Plays back a recorded session on the track map with full telemetry stats panel.
```bash
./replay.sh "Track Map Builds/track_0_true_map.json" telemetry/telemetry_20260317_133507.jsonl
```

**Controls:**
| Key | Action |
|-----|--------|
| `Space` | Play / pause |
| `Left` / `Right` | Skip -5s / +5s |
| `1` / `2` / `3` / `4` | Speed 1x / 2x / 4x / 0.5x |
| Click progress bar | Seek to position |
| Scroll / drag / `R` / `F` | Same as live map |

## Testing (No Game Required)

These scripts use a built-in UDP packet simulator.

```bash
./monitor_test.sh          # Test live monitor
./test_with_simulator.sh   # Test input monitor
./record_test.sh           # Test recording (30 seconds)
./track_map_gui_test.sh    # Test track map GUI
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
mvn -q exec:java -Dexec.mainClass="com.racingai.f1telemetry.F1TelemetryApp" | python3 -u track_map_live.py "Track Map Builds/track_0_true_map.json"

# Run the UDP packet simulator (for testing without the game)
mvn -q exec:java -Dexec.mainClass="com.racingai.f1telemetry.UDPPacketSender"
```

## Configuration

Edit `src/main/resources/application.properties`:

| Setting | Default | Description |
|---------|---------|-------------|
| `udp.port` | 20777 | UDP listening port |
| `output.rate.hz` | 30 | JSON output frame rate |
| `nearby.cars.max` | 6 | Max nearby cars in output |
| `nearby.cars.time.gap.seconds` | 1.5 | Time gap threshold (seconds) |

#Track List
Track 0 - Australia