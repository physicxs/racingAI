#!/bin/bash
# Test telemetry recorder with simulated F1 packets
# Records for 30 seconds then stops automatically

cd "$(dirname "$0")"

# Kill any existing processes
pkill -f "f1_receiver.py" 2>/dev/null
pkill -f "UDPPacketSender" 2>/dev/null
sleep 1

echo "╔════════════════════════════════════════════════════════════════════════════════╗"
echo "║ F1 2025 TELEMETRY RECORDER TEST (Simulated Data)                              ║"
echo "╚════════════════════════════════════════════════════════════════════════════════╝"
echo ""
echo "Starting packet simulator and recorder..."
echo "Will record for 30 seconds (or until Ctrl+C)"
echo ""

# Start packet sender in background
mvn -q exec:java -Dexec.mainClass="com.racingai.f1telemetry.UDPPacketSender" 2>/dev/null &
SENDER_PID=$!

# Give it a moment to start
sleep 2

# Start receiver with recorder (limit to 30 seconds for test)
(
    sleep 30
    kill $SENDER_PID 2>/dev/null
    pkill -f "f1_receiver.py" 2>/dev/null
) &
TIMER_PID=$!

python3 -u f1_receiver.py 2>&1 | python3 record_telemetry.py

# Clean up
kill $SENDER_PID 2>/dev/null
kill $TIMER_PID 2>/dev/null
