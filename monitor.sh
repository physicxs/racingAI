#!/bin/bash
# Live comprehensive telemetry monitor
# Shows track, position, inputs, tyre wear, and nearby cars at 10 Hz

cd "$(dirname "$0")"

# Kill any existing receiver
pkill -f "f1_receiver.py" 2>/dev/null
sleep 1

echo "═══════════════════════════════════════════════════════════════════════════════"
echo "  F1 2025 LIVE TELEMETRY MONITOR"
echo "═══════════════════════════════════════════════════════════════════════════════"
echo ""
echo "Starting receiver on UDP port 20777..."
echo ""
echo "Make sure F1 2025 is running with UDP telemetry enabled:"
echo "  Settings → Telemetry Settings → UDP Telemetry: ON"
echo "  UDP Port: 20777"
echo ""
echo "Starting in 2 seconds..."
sleep 2

python3 -u f1_receiver.py 2>&1 | python3 live_monitor.py
