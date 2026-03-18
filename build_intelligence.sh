#!/bin/bash
# Build track intelligence layer from an existing track map
# Usage: ./build_intelligence.sh <track_map.json> [-o output.json]

cd "$(dirname "$0")"

if [ -z "$1" ]; then
    echo "F1 2025 Track Intelligence Builder"
    echo "===================================="
    echo ""
    echo "Usage: ./build_intelligence.sh <track_map.json> [-o output.json]"
    echo ""
    echo "Computes curvature, corner detection, and target speed from a track map."
    echo ""
    echo "Example:"
    echo '  ./build_intelligence.sh "Track Map Builds/track_0_true_map.json"'
    exit 1
fi

python3 track_intelligence.py "$@"
