#!/bin/bash
# Record F1 2025 telemetry to JSONL file
# Saves to telemetry_YYYYMMDD_HHMMSS.jsonl

cd "$(dirname "$0")"

# Kill any existing receiver
pkill -f "f1telemetry.F1TelemetryApp" 2>/dev/null
sleep 1

echo "╔════════════════════════════════════════════════════════════════════════════════╗"
echo "║ F1 2025 TELEMETRY RECORDER                                                     ║"
echo "╚════════════════════════════════════════════════════════════════════════════════╝"
echo ""
echo "Starting receiver on UDP port 20777..."
echo ""
echo "Make sure F1 2025 is running with UDP telemetry enabled:"
echo "  Settings → Telemetry Settings → UDP Telemetry: ON"
echo "  UDP Port: 20777"
echo ""
echo "Press Ctrl+C to stop recording"
echo ""
echo "Starting in 2 seconds..."
sleep 2
echo ""

mvn -q exec:java -Dexec.mainClass="com.racingai.f1telemetry.F1TelemetryApp" 2>&1 | python3 record_telemetry.py
