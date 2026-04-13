#!/bin/bash
# Test track map builder with simulated F1 packets
# Records simulated telemetry, then builds map from it

cd "$(dirname "$0")"

# Kill any existing processes
pkill -f "f1_receiver.py" 2>/dev/null
pkill -f "UDPPacketSender" 2>/dev/null
sleep 1

echo "F1 2025 Track Map Builder - Test Mode"
echo "======================================"
echo ""
echo "Step 1: Recording 60 seconds of simulated telemetry..."
echo "  (Simulated oval track, ~2 laps)"
echo ""

JSONL_FILE="test_map_recording.jsonl"

# Start packet sender in background
mvn -q exec:java -Dexec.mainClass="com.racingai.f1telemetry.UDPPacketSender" 2>/dev/null &
SENDER_PID=$!
sleep 2

# Record for 60 seconds using a timeout
timeout 60 bash -c "python3 -u f1_receiver.py 2>&1 | python3 -c \"
import sys
count = 0
with open('$JSONL_FILE', 'w') as f:
    for line in sys.stdin:
        if line.startswith('{'):
            f.write(line)
            count += 1
            if count % 300 == 0:
                print(f'  Recorded {count} frames...', flush=True)
\""

# Clean up
kill $SENDER_PID 2>/dev/null
pkill -f "f1_receiver.py" 2>/dev/null
pkill -f "UDPPacketSender" 2>/dev/null

echo ""
echo "Step 2: Building track map..."
echo ""

python3 build_track_map.py "$JSONL_FILE" test_track_map.json

echo ""
echo "Done. Output: test_track_map.json"
