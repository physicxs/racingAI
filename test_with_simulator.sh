#!/bin/bash
# Test input monitor with simulated F1 packets (no game required)

cd "$(dirname "$0")"

# Kill any existing receiver
pkill -f "f1telemetry.F1TelemetryApp" 2>/dev/null
pkill -f "UDPPacketSender" 2>/dev/null
sleep 1

echo "Starting test with simulated F1 2025 packets..."
echo ""

# Start packet sender in background
mvn -q exec:java -Dexec.mainClass="com.racingai.f1telemetry.UDPPacketSender" &
SENDER_PID=$!

# Give it a moment to start
sleep 2

# Start receiver with monitor
mvn -q exec:java -Dexec.mainClass="com.racingai.f1telemetry.F1TelemetryApp" 2>&1 | python3 monitor_inputs.py

# Clean up
kill $SENDER_PID 2>/dev/null
