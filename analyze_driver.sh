#!/bin/bash
# Analyze driver performance against track intelligence
# Usage: ./analyze_driver.sh <intelligence.json> <telemetry.jsonl> [-o output.json]

cd "$(dirname "$0")"

if [ -z "$1" ] || [ -z "$2" ]; then
    echo "F1 2025 Player vs Track Analysis"
    echo "================================="
    echo ""
    echo "Usage: ./analyze_driver.sh <intelligence.json> <telemetry.jsonl> [-o output.json]"
    echo ""
    echo "Evaluates driver performance against the track intelligence model."
    echo ""
    echo "Example:"
    echo '  ./analyze_driver.sh "Track Map Builds/track_0_intelligence.json" telemetry/session.jsonl'
    exit 1
fi

python3 driver_analysis.py "$@"
