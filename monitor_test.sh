#!/bin/bash
# Test live monitor with simulated F1 packets

cd "$(dirname "$0")"

# Kill any existing processes
pkill -f "f1_receiver.py" 2>/dev/null
pkill -f "UDPPacketSender" 2>/dev/null
sleep 1

echo "═══════════════════════════════════════════════════════════════════════════════"
echo "  F1 2025 LIVE MONITOR TEST (Simulated Data)"
echo "═══════════════════════════════════════════════════════════════════════════════"
echo ""
echo "Starting packet simulator and receiver..."
echo ""

# Start packet sender in background
mvn -q exec:java -Dexec.mainClass="com.racingai.f1telemetry.UDPPacketSender" 2>/dev/null &
SENDER_PID=$!

# Give it a moment to start
sleep 2

# Start receiver with monitor
python3 -u f1_receiver.py 2>&1 | python3 live_monitor.py

# Clean up
kill $SENDER_PID 2>/dev/null
