# F1 2025 Telemetry Ingestion System

A Java application for receiving, decoding, and streaming F1 2025 UDP telemetry data.

**Status:** ✅ Complete | All 17 development phases finished | 21 unit tests passing

## Quick Start

**🎮 Live Monitor** - Real-time dashboard:
```bash
./monitor.sh
```

**💾 Record Session** - Save telemetry to file:
```bash
./record.sh
```

**🗺️ Build Track Map** - Generate 2D track map from recorded laps:
```bash
./build_true_centerline.sh <telemetry.jsonl>
```

**📍 Live Track Map GUI** - Real-time car position on track:
```bash
./track_map_gui.sh <track_map.json>
```

**🔄 Race Replay** - Replay a recorded race on the track map:
```bash
./replay.sh <track_map.json> <telemetry.jsonl>
```

**📊 Test Inputs** - Verify controls:
```bash
./test_inputs.sh
```

See [QUICK_START.md](QUICK_START.md) for detailed setup and usage. See [TRACK_MAP_GUIDE.md](TRACK_MAP_GUIDE.md) for track map generation. See [DERIVED_BATTLE_METRICS.md](DERIVED_BATTLE_METRICS.md) for racecraft AI battle metrics specification.

## Overview

This project handles telemetry data ingestion from F1 2025 via UDP, providing a clean JSON stream of racing data for analysis and processing.

### In Scope
- Receive F1 2025 UDP packets on port 20777
- Decode official 2025 packet structures
- Merge packets into a live state model
- Select nearby cars (up to 6 within 1.5s gap)
- Output newline-delimited JSON stream at 30 Hz

### Out of Scope
- Racing AI or decision-making logic
- Coaching or strategy recommendations
- Machine learning or predictive analytics

## Requirements

- Java 17 or higher
- Maven 3.6+
- F1 2025 game with UDP telemetry enabled
- Windows platform (for game integration)

## Project Structure

```
src/main/java/com/racingai/f1telemetry/
├── F1TelemetryApp.java          # Main application entry point
├── config/                       # Configuration loading
├── packets/                      # F1 2025 packet structure definitions
├── decoder/                      # UDP reception and binary decoding
├── state/                        # Live telemetry state management
├── output/                       # JSON stream generation (JSONL at 30 Hz)
└── utils/                        # Utility classes and helpers
```

## Configuration

Configuration is managed via `src/main/resources/application.properties`:

```properties
udp.port=20777                    # UDP listening port
output.rate.hz=30                 # JSON output frame rate
nearby.cars.max=6                 # Maximum nearby cars to include
nearby.cars.time.gap.seconds=1.5  # Time gap threshold for nearby cars
```

## F1 2025 Game Settings

Configure F1 2025 telemetry settings:
- **UDP Telemetry:** Enabled
- **UDP Format:** 2025
- **UDP Send Rate:** 30 Hz
- **UDP Port:** 20777
- **UDP IP Address:**
  - `127.0.0.1` if game and receiver on same machine
  - Your receiver's IP address (e.g., `192.168.1.116`) if on different machines

For detailed setup instructions including cross-machine configuration, see [TESTING.md](TESTING.md).

## Building

```bash
# Compile the project
mvn clean compile

# Run tests
mvn test

# Package into executable JAR
mvn package
```

## Running

```bash
# Run directly with Maven
mvn exec:java -Dexec.mainClass="com.racingai.f1telemetry.F1TelemetryApp"

# Or run the packaged JAR
java -jar target/f1-telemetry-ingestion-1.0.0-SNAPSHOT.jar
```

## Testing

The system can be tested with:
1. **Simulated packets** - Use `UDPPacketSender` to send mock F1 2025 packets (no game required)
2. **Real F1 2025 game** - Works on same machine or across network

See [TESTING.md](TESTING.md) for complete testing instructions including:
- Same-machine setup
- Cross-machine/network setup
- Troubleshooting guide

## Development Phases

- [x] **Phase 1:** Project setup and structure
- [x] **Phase 2:** Packet format definitions
- [x] **Phase 3:** UDP receiver
- [x] **Phase 4:** Packet decoder and validation
- [x] **Phase 5:** State management
- [x] **Phase 6:** Nearby cars selection logic
- [x] **Phase 7:** JSON output stream
- [x] **Phase 8:** Integration and main loop
- [x] **Phase 9:** Testing and validation
- [x] **Phase 10:** Live Dashboard & Save to File
- [x] **Phase 11:** Track Map Generation
- [x] **Phase 12:** Racecraft AI Telemetry (orientation, DRS/ERS, tyre data, damage, flags, stats panel)
- [x] **Phase 13:** Accurate Car Positioning (segment-based projection, true lateral offset, debug validation)
- [x] **Phase 14:** True Track Centerline (edge detection from multi-lap data, per-point variable track width)
- [x] **Phase 15:** Edge Noise Cleanup (speed filter, 2-sigma outlier removal, weighted percentiles, edge smoothing, width clamping)
- [x] **Phase 16:** Adaptive Edge Reconstruction (per-bin confidence tiers, low-confidence interpolation, corrected pipeline ordering)
- [x] **Phase 17:** Spline-Based Track Model (Catmull-Rom spline centerline, geometry-driven edges, separated width smoothing)

## Output Format

The application outputs newline-delimited JSON (JSONL) at 30 Hz. Each line contains:

```json
{
  "timestamp": 1771034117788,
  "sessionTime": 421.569,
  "frameId": 17647,
  "meta": {
    "track_id": 5,
    "track_length": 5303,
    "safety_car": 0,
    "weather": 0,
    "track_temp": 35,
    "air_temp": 22,
    "total_laps": 58
  },
  "player": {
    "position": 9,
    "lapNumber": 5,
    "lapDistance": 1.4140625,
    "speed": 304,
    "gear": 8,
    "throttle": 1.0,
    "brake": 0.0,
    "steering": 0.000820861,
    "tyreWear": { "rearLeft": 13.5, "rearRight": 9.8, "frontLeft": 13.5, "frontRight": 5.8 },
    "world_pos_m": { "x": 100.5, "y": 5.2, "z": 200.3 },
    "yaw": 0.1, "pitch": 0.02, "roll": -0.01,
    "gForceLateral": 0.5, "gForceLongitudinal": 1.2,
    "drs": 0, "drsAllowed": 1,
    "ersDeployMode": 1, "ersStoreEnergy": 2000000.0,
    "ersDeployedThisLap": 500000.0,
    "tyreSurfaceTemp": [92, 93, 95, 97],
    "tyreInnerTemp": [100, 101, 102, 103],
    "tyreCompound": 18, "tyreCompoundVisual": 16, "tyresAgeLaps": 12,
    "tyreDamage": [0, 0, 0, 0],
    "brakeTemp": [400, 410, 420, 430],
    "floorDamage": 0, "diffuserDamage": 0, "sidepodDamage": 0,
    "vehicleFiaFlags": 0
  },
  "nearbyCars": [
    {
      "carIndex": 0,
      "position": 10,
      "gap": 0.228,
      "world_pos_m": {
        "x": 123.45,
        "y": 1.23,
        "z": 456.78
      }
    }
  ]
}
```

**Fields:**
- `timestamp`: Unix timestamp (milliseconds)
- `sessionTime`: Game session time (seconds)
- `frameId`: Game frame identifier
- `meta`: Session metadata
  - `track_id`, `track_length`: Track identifier and length (meters)
  - `safety_car`: 0=none, 1=full SC, 2=VSC, 3=formation
  - `weather`: 0=clear, 1=light cloud, 2=overcast, 3=light rain, 4=heavy rain, 5=storm
  - `track_temp`, `air_temp`: Temperatures (°C)
  - `total_laps`: Total race laps
- `player`: Player car telemetry
  - Inputs: `steering`, `throttle`, `brake`
  - State: `position`, `lapNumber`, `lapDistance`, `speed`, `gear`
  - Tyre wear: all four tyres (percentage) via `tyreWear` object
  - `world_pos_m`: 3D world position (x, y, z in meters)
  - Orientation: `yaw`, `pitch`, `roll` (radians)
  - G-forces: `gForceLateral`, `gForceLongitudinal`
  - DRS: `drs` (0/1), `drsAllowed` (0/1)
  - ERS: `ersDeployMode` (0-3), `ersStoreEnergy` (joules), `ersDeployedThisLap`
  - Tyres: `tyreSurfaceTemp`, `tyreInnerTemp` (arrays [RL,RR,FL,FR] in °C)
  - Compound: `tyreCompoundVisual` (16=soft, 17=medium, 18=hard), `tyresAgeLaps`
  - Damage: `floorDamage`, `diffuserDamage`, `sidepodDamage`, `tyreDamage`
  - Brake temps: `brakeTemp` (array [RL,RR,FL,FR] in °C)
  - Flags: `vehicleFiaFlags` (0=none, 1=green, 2=blue, 3=yellow)
- `nearbyCars`: Up to 6 cars within 1.5s gap
  - `carIndex`, `position`, `gap` (seconds)
  - `world_pos_m`: 3D position (x, y, z in meters)

## Known Issues

The F1 2025 UDP spec has a known issue where `LapData.m_gridPosition` and `LapData.m_driverStatus` may be swapped. This application detects and handles this automatically via range validation.

## License

See project documentation for details.
