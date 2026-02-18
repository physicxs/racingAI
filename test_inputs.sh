#!/bin/bash
# Live input monitor - displays steering, throttle, brake, clutch, gear, speed at 10 Hz

cd "$(dirname "$0")"

# Kill any existing receiver
pkill -f "f1telemetry.F1TelemetryApp" 2>/dev/null
sleep 1

echo "Starting telemetry receiver..."
echo "Waiting for F1 2025 telemetry packets on UDP port 20777..."
echo ""
echo "Make sure F1 2025 is running and UDP telemetry is enabled!"
echo "Settings -> Telemetry Settings -> UDP Telemetry: ON"
echo "UDP Port: 20777"
echo ""
echo "Press Ctrl+C to stop"
echo ""

mvn -q exec:java -Dexec.mainClass="com.racingai.f1telemetry.F1TelemetryApp" 2>&1 | python3 monitor_inputs.py
