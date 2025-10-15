#!/usr/bin/env python3
"""
Count volumes per series in the database
"""

import json
from collections import defaultdict

def main():
    try:
        with open('project_state.json', 'r') as f:
            state = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"Error loading project_state.json: {e}")
        return

    series_counts = defaultdict(int)

    for api_call in state.get('api_calls', []):
        if api_call.get('success', False):
            try:
                response = json.loads(api_call['response'])
                series = response.get('series_name')
                if series:
                    series_counts[series] += 1
            except json.JSONDecodeError:
                continue

    print("Volumes per series in database:")
    print("=" * 50)
    total_volumes = 0
    for series, count in sorted(series_counts.items()):
        print(f"{series}: {count} volumes")
        total_volumes += count

    print("=" * 50)
    print(f"Total volumes: {total_volumes}")

if __name__ == "__main__":
    main()