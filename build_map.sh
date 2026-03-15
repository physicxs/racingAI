#!/bin/bash
# Build a track map from recorded telemetry JSONL
# Usage: ./build_map.sh <telemetry.jsonl> [output.json]

cd "$(dirname "$0")"

if [ -z "$1" ]; then
    echo "F1 2025 Track Map Builder"
    echo "========================="
    echo ""
    echo "Usage: ./build_map.sh <telemetry.jsonl> [output.json]"
    echo ""
    echo "Build a 2D track map from recorded telemetry data."
    echo "Record telemetry first using: ./record.sh"
    echo ""
    echo "Examples:"
    echo "  ./build_map.sh telemetry_20260312_143000.jsonl"
    echo "  ./build_map.sh telemetry_20260312_143000.jsonl melbourne_map.json"
    exit 1
fi

python3 build_track_map.py "$@"
