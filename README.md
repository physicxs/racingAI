# F1 2025 Telemetry Ingestion System

A Java application for receiving, decoding, and streaming F1 2025 UDP telemetry data.

**Status:** ✅ Complete | All 9 development phases finished | 19 unit tests passing

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

## Output Format

The application outputs newline-delimited JSON (JSONL) at 30 Hz. Each line contains:

```json
{
  "timestamp": 1771034117788,
  "sessionTime": 421.569,
  "frameId": 17647,
  "meta": {
    "track_id": 5
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
- `meta.track_id`: Track identifier (-1 if unknown)
- `player`: Player car telemetry
  - Inputs: steering, throttle, brake
  - State: position, lapNumber, lapDistance, speed, gear
  - Tyre wear: all four tyres (percentage)
- `nearbyCars`: Up to 6 cars within 1.5s gap
  - `carIndex`, `position`, `gap` (seconds)
  - `world_pos_m`: 3D position (x, y, z in meters)

## Known Issues

The F1 2025 UDP spec has a known issue where `LapData.m_gridPosition` and `LapData.m_driverStatus` may be swapped. This application detects and handles this automatically via range validation.

## License

See project documentation for details.
