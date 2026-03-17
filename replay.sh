#!/bin/bash
# Replay a recorded race on the track map
# Usage: ./replay.sh <track_map.json> <telemetry.jsonl>

cd "$(dirname "$0")"

if [ -z "$1" ] || [ -z "$2" ]; then
    echo "F1 2025 Race Replay"
    echo "==================="
    echo ""
    echo "Usage: ./replay.sh <track_map.json> <telemetry.jsonl>"
    echo ""
    echo "Replay a recorded race on the track map."
    echo ""
    echo "Steps:"
    echo "  1. Record a race:  ./record.sh"
    echo "  2. Build map:      ./build_map.sh <recording.jsonl>"
    echo "  3. Replay:         ./replay.sh <track_map.json> <recording.jsonl>"
    echo ""
    echo "Controls:"
    echo "  Space           Play / pause"
    echo "  Left / Right    Skip -5s / +5s"
    echo "  1 / 2 / 3 / 4  Speed 1x / 2x / 4x / 0.5x"
    echo "  Click bar       Seek to position"
    echo "  Scroll wheel    Zoom in/out"
    echo "  Click + drag    Pan the map"
    echo "  R               Reset zoom"
    echo "  F               Follow player"
    echo ""
    echo "Example:"
    echo "  ./replay.sh track_0_map.json telemetry_20260315_105017.jsonl"
    exit 1
fi

MAP_FILE="$1"
REPLAY_FILE="$2"

if [ ! -f "$MAP_FILE" ]; then
    echo "ERROR: Track map file not found: $MAP_FILE"
    exit 1
fi

if [ ! -f "$REPLAY_FILE" ]; then
    echo "ERROR: Telemetry file not found: $REPLAY_FILE"
    exit 1
fi

EXTRA_ARGS="${@:3}"
python3 track_map_live.py "$MAP_FILE" --replay "$REPLAY_FILE" $EXTRA_ARGS
