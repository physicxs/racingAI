#!/bin/bash
# Test the live track map GUI with simulated packets
# Generates a test track map, then shows the GUI with a moving car

cd "$(dirname "$0")"

# Kill any existing processes
pkill -f "f1telemetry.F1TelemetryApp" 2>/dev/null
pkill -f "UDPPacketSender" 2>/dev/null
sleep 1

MAP_FILE="test_track_map.json"

echo "F1 2025 Track Map GUI - Test Mode"
echo "=================================="
echo ""

# Check if test map exists, generate if not
if [ ! -f "$MAP_FILE" ]; then
    echo "Step 1: Generating test track map..."
    echo "  Recording 30 seconds of simulated telemetry..."

    JSONL_FILE="test_map_recording.jsonl"

    # Start packet sender in background
    mvn -q exec:java -Dexec.mainClass="com.racingai.f1telemetry.UDPPacketSender" 2>/dev/null &
    SENDER_PID=$!
    sleep 2

    # Record for 30 seconds
    timeout 30 bash -c "mvn -q exec:java -Dexec.mainClass=\"com.racingai.f1telemetry.F1TelemetryApp\" 2>&1 | python3 -c \"
import sys
count = 0
with open('$JSONL_FILE', 'w') as f:
    for line in sys.stdin:
        if line.startswith('{'):
            f.write(line)
            count += 1
            if count % 300 == 0:
                print(f'  {count} frames...', flush=True)
\""

    kill $SENDER_PID 2>/dev/null
    pkill -f "f1telemetry.F1TelemetryApp" 2>/dev/null
    pkill -f "UDPPacketSender" 2>/dev/null
    sleep 1

    echo "  Building track map..."
    python3 build_track_map.py "$JSONL_FILE" "$MAP_FILE"
    echo ""
fi

echo "Step 2: Starting GUI with simulated car..."
echo "  Close the GUI window or press Ctrl+C to stop."
echo ""

# Start packet sender in background
mvn -q exec:java -Dexec.mainClass="com.racingai.f1telemetry.UDPPacketSender" 2>/dev/null &
SENDER_PID=$!
sleep 2

# Start receiver piped to GUI
mvn -q exec:java -Dexec.mainClass="com.racingai.f1telemetry.F1TelemetryApp" 2>&1 | python3 track_map_live.py "$MAP_FILE"

# Clean up
kill $SENDER_PID 2>/dev/null
pkill -f "UDPPacketSender" 2>/dev/null
