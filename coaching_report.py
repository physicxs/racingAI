#!/usr/bin/env python3
"""
F1 2025 Coaching Report

Generates per-corner coaching feedback from driver analysis data.

Usage:
    python3 coaching_report.py <driver_analysis.json> [-o output.json]
"""

import json
import sys
import os


# ─── Thresholds ──────────────────────────────────────────────────────────────

ENTRY_SPEED_DELTA = 5.0      # m/s
APEX_LATERAL = 1.5           # meters (signed)
EXIT_SPEED_DELTA = 5.0       # m/s
EXIT_THROTTLE = 0.8


def generate_coaching(analysis_path):
    """Generate per-corner coaching from driver analysis."""

    with open(analysis_path) as f:
        analysis = json.load(f)

    corners = analysis['corners']
    report = []

    for corner in corners:
        cid = corner['corner_id']
        issues = []

        # ── Entry ────────────────────────────────────────────────────
        entry_delta = corner['avg_entry_speed_delta']

        if entry_delta < -ENTRY_SPEED_DELTA:
            issues.append({
                'phase': 'entry',
                'type': 'early_braking',
                'message': 'Braking too early',
                'detail': f'Avg entry speed {abs(entry_delta):.1f} m/s below target',
            })
        elif entry_delta > ENTRY_SPEED_DELTA:
            issues.append({
                'phase': 'entry',
                'type': 'late_braking',
                'message': 'Braking too late',
                'detail': f'Avg entry speed {entry_delta:.1f} m/s above target',
            })

        # ── Apex ─────────────────────────────────────────────────────
        apex_lateral = corner['avg_apex_lateral']

        if apex_lateral > APEX_LATERAL:
            issues.append({
                'phase': 'apex',
                'type': 'apex_too_left',
                'message': 'Too far left at apex',
                'detail': f'Avg lateral offset {apex_lateral:+.1f}m from centerline',
            })
        elif apex_lateral < -APEX_LATERAL:
            issues.append({
                'phase': 'apex',
                'type': 'apex_too_right',
                'message': 'Too far right at apex',
                'detail': f'Avg lateral offset {apex_lateral:+.1f}m from centerline',
            })

        # ── Exit ─────────────────────────────────────────────────────
        exit_delta = corner['avg_exit_speed_delta']
        exit_throttle = corner['avg_exit_throttle']

        if exit_delta < -EXIT_SPEED_DELTA:
            issues.append({
                'phase': 'exit',
                'type': 'poor_exit_speed',
                'message': 'Poor exit speed',
                'detail': f'Avg exit speed {abs(exit_delta):.1f} m/s below target',
            })

        if exit_throttle < EXIT_THROTTLE:
            issues.append({
                'phase': 'exit',
                'type': 'late_throttle',
                'message': 'Late throttle application',
                'detail': f'Avg exit throttle {exit_throttle:.0%} (target ≥{EXIT_THROTTLE:.0%})',
            })

        # ── Summary ──────────────────────────────────────────────────
        if not issues:
            summary = 'Clean corner — no issues detected'
        else:
            parts = [i['message'] for i in issues]
            summary = '; '.join(parts)

        report.append({
            'corner_id': cid,
            'issues': issues,
            'summary': summary,
        })

    return {
        'track_id': analysis.get('track_id'),
        'telemetry_file': analysis.get('telemetry_file'),
        'corners_analyzed': len(report),
        'corners_with_issues': sum(1 for r in report if r['issues']),
        'corners_clean': sum(1 for r in report if not r['issues']),
        'corners': report,
    }


def main():
    output_path = None
    analysis_path = None

    args = sys.argv[1:]
    i = 0
    while i < len(args):
        if args[i] == '-o' and i + 1 < len(args):
            output_path = args[i + 1]
            i += 2
        elif args[i].startswith('-'):
            print(f"Unknown option: {args[i]}")
            sys.exit(1)
        else:
            analysis_path = args[i]
            i += 1

    if not analysis_path:
        print("F1 2025 Coaching Report")
        print("=" * 40)
        print()
        print("Usage: python3 coaching_report.py <driver_analysis.json> [-o output.json]")
        print()
        print("Example:")
        print('  python3 coaching_report.py "Track Map Builds/track_0_driver_analysis.json"')
        sys.exit(1)

    print("F1 2025 Coaching Report")
    print("=" * 40)

    result = generate_coaching(analysis_path)

    # Print report
    print(f"\nTrack {result['track_id']} — {result['corners_analyzed']} corners analyzed")
    print(f"  Clean: {result['corners_clean']}  |  Issues: {result['corners_with_issues']}")
    print()

    for corner in result['corners']:
        cid = corner['corner_id']
        if corner['issues']:
            print(f"  Corner {cid}:")
            for issue in corner['issues']:
                print(f"    [{issue['phase'].upper():>5}] {issue['message']} — {issue['detail']}")
        else:
            print(f"  Corner {cid}: Clean")

    # Save
    out_dir = "Track Map Builds"
    os.makedirs(out_dir, exist_ok=True)
    if output_path is None:
        track_id = result.get('track_id')
        track_name = f"track_{track_id}" if track_id is not None else "track_unknown"
        output_path = os.path.join(out_dir, f"{track_name}_coaching_report.json")

    with open(output_path, 'w') as f:
        json.dump(result, f, indent=2)

    print(f"\nCoaching report written to {output_path}")


if __name__ == '__main__':
    main()
