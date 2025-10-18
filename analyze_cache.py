#!/usr/bin/env python3
"""
Analyze Manga Cache

Analyze what manga series and volumes are currently cached.
"""

import os
import sys
from collections import defaultdict

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(__file__))

from manga_lookup import ProjectState


def analyze_cache():
    """Analyze the current cache contents"""
    project_state = ProjectState()

    print("📊 Manga Cache Analysis")
    print("=" * 60)

    # Basic stats
    print(f"Total API calls: {len(project_state.state['api_calls'])}")
    print(f"Cached responses: {len(project_state.state['cached_responses'])}")
    print(f"Total books found: {project_state.state['total_books_found']}")
    print(f"Interaction count: {project_state.state['interaction_count']}")

    # Analyze cached responses
    series_volumes = defaultdict(list)

    for cache_key, response in project_state.state["cached_responses"].items():
        try:
            # Parse the cache key format: "prompt_hash_volume"
            if "_" in cache_key:
                parts = cache_key.split("_")
                if len(parts) >= 2:
                    volume = parts[-1]  # Last part is volume number
                    # The prompt part contains the series name
                    prompt_part = " ".join(parts[:-1])

                    # Try to extract series name from prompt
                    if "manga series" in prompt_part.lower():
                        # Extract text between quotes or after "manga series"
                        import re
                        match = re.search(r'manga series[\"\']?([^\"\']+)[\"\']?', prompt_part.lower())
                        if match:
                            series_name = match.group(1).strip()
                        else:
                            # Fallback: take first few words
                            series_name = " ".join(prompt_part.split()[:3])
                    else:
                        series_name = " ".join(prompt_part.split()[:3])

                    series_volumes[series_name].append(volume)

        except Exception:
            continue

    print("\n📚 Cached Series and Volumes:")
    print("-" * 40)

    for series, volumes in sorted(series_volumes.items()):
        print(f"{series}:")
        print(f"  Volumes: {', '.join(sorted(volumes))}")
        print(f"  Total: {len(volumes)} volumes")
        print()

    # Show recent searches
    print("\n🔍 Recent Searches:")
    print("-" * 40)
    for search in project_state.state["searches"][-5:]:  # Last 5 searches
        print(f"Query: {search['query']}")
        print(f"Books found: {search['books_found']}")
        print(f"Timestamp: {search['timestamp']}")
        print()


if __name__ == "__main__":
    analyze_cache()
