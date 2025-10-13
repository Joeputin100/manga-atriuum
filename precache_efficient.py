#!/usr/bin/env python3
"""
Efficient Manga Series Precaching

Precaches data for all extant English language paperback volumes,
using existing cache and only fetching missing volumes.
"""

import sys
import os
import time
from typing import Dict, List

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(__file__))

from manga_lookup import DeepSeekAPI, ProjectState, process_book_data


# Series to precache with estimated volume counts
SERIES_TO_PRECACHE = {
    "Tokyo Ghoul": 14,
    "Tokyo Ghoul:re": 16,
    "Naruto": 72,
    "Boruto: Naruto The Next Generation": 20,
    "Boruto: Two Blue Vortex": 5,
    "Assassination Classroom": 21,
    "Akira": 6,
    "Noragami: Stray God": 26,
    "Black Clover": 35,
    "Fairy Tail": 63,
    "Cells At Work": 6,
    "One Piece": 105,
    "Bleach": 74,
    "Children of Whales": 23,
    "Tegami Bachi": 20,
    "Death Note": 12,
    "Bakuman": 20,
    "A Silent Voice": 7,
    "Haikyu!!": 45
}


def check_existing_cache(series_name: str, max_volumes: int, deepseek_api: DeepSeekAPI, project_state: ProjectState) -> List[int]:
    """Check which volumes are already cached"""
    cached_volumes = []
    missing_volumes = []

    for volume in range(1, max_volumes + 1):
        prompt = deepseek_api._create_comprehensive_prompt(series_name, volume)
        cached_response = project_state.get_cached_response(prompt, volume)

        if cached_response:
            cached_volumes.append(volume)
        else:
            missing_volumes.append(volume)

    return cached_volumes, missing_volumes


def precache_missing_volumes(series_name: str, missing_volumes: List[int], deepseek_api: DeepSeekAPI, project_state: ProjectState) -> Dict[str, int]:
    """Precache missing volumes for a series"""
    successful = 0
    failed = 0

    for volume in missing_volumes:
        try:
            print(f"    Volume {volume}...", end=" ")

            # Fetch fresh data
            book_data = deepseek_api.get_book_info(series_name, volume, project_state)

            if book_data:
                book = process_book_data(book_data, volume)
                print("✓")
                successful += 1

                # Add delay to respect rate limits
                time.sleep(0.5)
            else:
                print("✗ (not found)")
                failed += 1

        except Exception as e:
            print(f"✗ (error: {str(e)[:50]})")
            failed += 1
            continue

    return {"successful": successful, "failed": failed}


def main():
    """Main function to precache all series efficiently"""
    print("🚀 Efficient Manga Series Precaching")
    print("=" * 60)

    # Initialize APIs
    try:
        deepseek_api = DeepSeekAPI()
        project_state = ProjectState()
    except Exception as e:
        print(f"❌ Failed to initialize APIs: {e}")
        return

    total_series = len(SERIES_TO_PRECACHE)
    total_cached = 0
    total_fetched = 0
    total_failed = 0

    print(f"Analyzing cache for {total_series} manga series...")
    print("=" * 60)

    # Process each series
    for series_name, max_volumes in SERIES_TO_PRECACHE.items():
        print(f"\n📚 {series_name} (volumes 1-{max_volumes})")

        # Check existing cache
        cached_volumes, missing_volumes = check_existing_cache(series_name, max_volumes, deepseek_api, project_state)

        print(f"  Cached: {len(cached_volumes)} volumes")
        print(f"  Missing: {len(missing_volumes)} volumes")

        total_cached += len(cached_volumes)

        # Precache missing volumes
        if missing_volumes:
            print(f"  Precaching missing volumes...")
            results = precache_missing_volumes(series_name, missing_volumes, deepseek_api, project_state)
            total_fetched += results["successful"]
            total_failed += results["failed"]
        else:
            print(f"  ✓ All volumes already cached")

    # Print summary
    print("\n" + "=" * 60)
    print("📊 Precaching Summary")
    print("=" * 60)
    print(f"Series processed: {total_series}")
    print(f"Volumes already cached: {total_cached}")
    print(f"Volumes newly fetched: {total_fetched}")
    print(f"Volumes failed/not found: {total_failed}")
    print(f"Total volumes in cache: {total_cached + total_fetched}")
    print(f"Total API calls made: {len(project_state.state['api_calls'])}")

    # Save final state
    project_state.save_state()
    print(f"\n💾 Project state saved to {project_state.state_file}")

    print("\n✅ Efficient precaching completed!")
    print("\nNext steps:")
    print("1. Use manga_lookup.py to search for specific volumes")
    print("2. Export to MARC format using the 'm' option")
    print("3. Check project_state.json for cached data")


if __name__ == "__main__":
    main()