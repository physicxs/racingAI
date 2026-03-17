#!/bin/bash
# Build a true track centerline from multi-lap telemetry
# Usage: ./build_true_centerline.sh <file1.jsonl> [file2.jsonl ...] [-o output.json]

cd "$(dirname "$0")"

if [ -z "$1" ]; then
    echo "F1 2025 True Track Centerline Builder"
    echo "======================================"
    echo ""
    echo "Usage: ./build_true_centerline.sh <file1.jsonl> [file2.jsonl ...] [-o output.json]"
    echo ""
    echo "Build a true geometric centerline from track edges."
    echo "For best results, record 3-5 laps with varied lateral positions:"
    echo "  - Some laps staying left"
    echo "  - Some laps staying right"
    echo "  - Some laps on the normal racing line"
    echo ""
    echo "Examples:"
    echo "  ./build_true_centerline.sh race.jsonl"
    echo "  ./build_true_centerline.sh left.jsonl right.jsonl normal.jsonl"
    echo "  ./build_true_centerline.sh race.jsonl -o monaco_true_map.json"
    exit 1
fi

python3 build_true_centerline.py "$@"
