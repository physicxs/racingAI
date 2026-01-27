# F1 2025 Telemetry Ingestion System

A Java application for receiving, decoding, and streaming F1 2025 UDP telemetry data.

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
├── packets/                      # F1 2025 packet structure definitions
├── decoder/                      # UDP reception and binary decoding
├── state/                        # Live telemetry state management
├── output/                       # JSON stream generation
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

## Development Phases

- [x] **Phase 1:** Project setup and structure
- [ ] **Phase 2:** Packet format definitions
- [ ] **Phase 3:** UDP receiver
- [ ] **Phase 4:** Packet decoder and validation
- [ ] **Phase 5:** State management
- [ ] **Phase 6:** Nearby cars selection logic
- [ ] **Phase 7:** JSON output stream
- [ ] **Phase 8:** Integration and main loop
- [ ] **Phase 9:** Testing and validation

## Output Format

The application outputs newline-delimited JSON (JSONL) at 30 Hz, with each line containing:
- Player inputs (steering, throttle, brake, gear, speed)
- Player position and lap distance
- Nearby cars list (up to 6 cars)
- Tyre wear data (where available)
- Session metadata

## Known Issues

The F1 2025 UDP spec has a known issue where `LapData.m_gridPosition` and `LapData.m_driverStatus` may be swapped. This application detects and handles this automatically via range validation.

## License

See project documentation for details.
