#!/bin/bash
# Live track map GUI - shows car position on track in real time
# Usage: ./track_map_gui.sh <track_map.json>

cd "$(dirname "$0")"

if [ -z "$1" ]; then
    echo "F1 2025 Live Track Map"
    echo "======================"
    echo ""
    echo "Usage: ./track_map_gui.sh <track_map.json>"
    echo ""
    echo "Show a real-time track map with your car's live position."
    echo "Requires a pre-built track map (see ./build_map.sh)."
    echo ""
    echo "Steps:"
    echo "  1. Record laps:    ./record.sh"
    echo "  2. Build map:      ./build_map.sh <recording.jsonl>"
    echo "  3. Run live GUI:   ./track_map_gui.sh <track_map.json>"
    echo ""
    echo "Example:"
    echo "  ./track_map_gui.sh track_0_map.json"
    exit 1
fi

MAP_FILE="$1"

if [ ! -f "$MAP_FILE" ]; then
    echo "ERROR: Track map file not found: $MAP_FILE"
    exit 1
fi

# Kill any existing receiver holding port 20777
pkill -9 -f "f1telemetry.F1TelemetryApp" 2>/dev/null
# Also kill by port in case pkill missed it
lsof -t -i :20777 2>/dev/null | xargs kill -9 2>/dev/null
sleep 1

echo "F1 2025 Live Track Map"
echo "======================"
echo ""
echo "Track map: $MAP_FILE"
echo ""
echo "Setup in F1 2025:"
echo "  UDP Telemetry: Enabled"
echo "  UDP Send Rate: 30 Hz"
echo "  UDP Port: 20777"
echo "  UDP IP: 127.0.0.1 (or this machine's IP)"
echo ""
mkdir -p telemetry
RECORD_FILE="telemetry/telemetry_$(date +%Y%m%d_%H%M%S).jsonl"

echo "Starting receiver and GUI..."
echo "Recording to: $RECORD_FILE"
echo ""
echo "To replay after the session:"
echo "  ./replay.sh $MAP_FILE $RECORD_FILE"
echo ""
echo "Close the GUI window or press Ctrl+C to stop."
echo ""

EXTRA_ARGS="${@:2}"
mvn -q exec:java -Dexec.mainClass="com.racingai.f1telemetry.F1TelemetryApp" | tee "$RECORD_FILE" | python3 -u track_map_live.py "$MAP_FILE" $EXTRA_ARGS
