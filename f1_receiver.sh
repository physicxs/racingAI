#!/bin/bash
# F1 2025 Telemetry Receiver (Python)
# Drop-in replacement for: mvn -q exec:java -Dexec.mainClass="com.racingai.f1telemetry.F1TelemetryApp"
#
# Usage: ./f1_receiver.sh [--port PORT]

cd "$(dirname "$0")"
python3 -u f1_receiver.py "$@"
