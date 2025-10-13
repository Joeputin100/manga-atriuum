#!/usr/bin/env python3
"""
Focused Manga Series Caching

Precaches the most important volumes (1-10) for each requested series first,
then continues with remaining volumes. This ensures core volumes are cached quickly.
"""

import sys
import os
import time
from typing import List, Dict

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(__file__))

from manga_lookup import DeepSeekAPI, ProjectState, process_book_data


# Requested series with core volumes (1-10) first, then remaining
REQUESTED_SERIES = {
    "Naruto": {"core": 10, "remaining": 62},  # 72 total
    "Boruto: Two Blue Vortex": {"core": 5, "remaining": 0},  # 5 total
    "Boruto: Naruto The Next Generation": {"core": 10, "remaining": 10},  # 20 total
    "Bleach": {"core": 10, "remaining": 64},  # 74 total
    "One Piece": {"core": 10, "remaining": 95},  # 105 total
    "Black Clover": {"core": 10, "remaining": 25},  # 35 total
    "Tokyo Ghoul": {"core": 10, "remaining": 4},  # 14 total
    "Tokyo Ghoul:re": {"core": 10, "remaining": 6},  # 16 total
    "Assassination Classroom": {"core": 10, "remaining": 11},  # 21 total
    "Akira": {"core": 6, "remaining": 0},  # 6 total
    "My Hero Academia": {"core": 10, "remaining": 30},  # 40 total
    "Fairy Tail": {"core": 10, "remaining": 53},  # 63 total
    "Attack on Titan": {"core": 10, "remaining": 24},  # 34 total
    "Tegami Bachi": {"core": 10, "remaining": 10},  # 20 total
    "Magus of the Library": {"core": 7, "remaining": 0},  # 7 total
    "Chainsaw Man": {"core": 10, "remaining": 5},  # 15 total
    "Dragon Ball Z": {"core": 10, "remaining": 16},  # 26 total
}


def precache_series_volumes(series_name: str, start_volume: int, end_volume: int, project_state: ProjectState, deepseek_api: DeepSeekAPI):
    """Precache data for a range of volumes in a manga series"""
    successful_volumes = 0
    failed_volumes = 0

    for volume in range(start_volume, end_volume + 1):
        try:
            print(f"  Volume {volume}...", end=" ")

            # Check if already cached
            prompt = deepseek_api._create_comprehensive_prompt(series_name, volume)
            cached_response = project_state.get_cached_response(prompt, volume)

            if cached_response:
                print("✓ (cached)")
                successful_volumes += 1
                continue

            # Fetch fresh data
            book_data = deepseek_api.get_book_info(series_name, volume, project_state)

            if book_data:
                book = process_book_data(book_data, volume)
                print("✓")
                successful_volumes += 1

                # Add small delay to respect rate limits
                time.sleep(0.5)
            else:
                print("✗ (not found)")
                failed_volumes += 1

                # If volume not found, assume series has fewer volumes
                if failed_volumes >= 3:
                    print(f"  Stopping at volume {volume} (multiple failures)")
                    break

        except Exception as e:
            print(f"✗ (error: {str(e)[:50]})")
            failed_volumes += 1
            continue

    return successful_volumes, failed_volumes


def main():
    """Main function to precache series in focused approach"""
    print("🚀 Starting Focused Manga Series Precaching")
    print("=" * 60)
    print("Strategy: Cache volumes 1-10 for each series first, then remaining volumes")
    print("=" * 60)

    # Initialize APIs
    try:
        deepseek_api = DeepSeekAPI()
        project_state = ProjectState()
    except Exception as e:
        print(f"❌ Failed to initialize APIs: {e}")
        return

    total_series = len(REQUESTED_SERIES)
    total_successful = 0
    total_failed = 0

    print(f"\nPhase 1: Caching Core Volumes (1-10) for {total_series} series...")
    print("=" * 60)

    # Phase 1: Cache core volumes (1-10) for each series
    for series_name, volumes in REQUESTED_SERIES.items():
        core_volumes = volumes["core"]
        print(f"\n📚 Precaching {series_name} (volumes 1-{core_volumes})...")

        successful, failed = precache_series_volumes(series_name, 1, core_volumes, project_state, deepseek_api)
        total_successful += successful
        total_failed += failed

    # Print intermediate summary
    print("\n" + "=" * 60)
    print("📊 Phase 1 Summary")
    print("=" * 60)
    print(f"Series processed: {total_series}")
    print(f"Core volumes cached: {total_successful}")
    print(f"Volumes failed/not found: {total_failed}")

    # Phase 2: Cache remaining volumes for series that have them
    print("\n" + "=" * 60)
    print("Phase 2: Caching Remaining Volumes...")
    print("=" * 60)

    remaining_successful = 0
    remaining_failed = 0

    for series_name, volumes in REQUESTED_SERIES.items():
        remaining_volumes = volumes["remaining"]
        if remaining_volumes > 0:
            start_volume = volumes["core"] + 1
            end_volume = volumes["core"] + remaining_volumes
            print(f"\n📚 Precaching {series_name} (volumes {start_volume}-{end_volume})...")

            successful, failed = precache_series_volumes(series_name, start_volume, end_volume, project_state, deepseek_api)
            remaining_successful += successful
            remaining_failed += failed

    # Final summary
    total_successful += remaining_successful
    total_failed += remaining_failed

    print("\n" + "=" * 60)
    print("📊 Final Precaching Summary")
    print("=" * 60)
    print(f"Series processed: {total_series}")
    print(f"Total volumes cached: {total_successful}")
    print(f"Total volumes failed/not found: {total_failed}")
    print(f"Total API calls made: {len(project_state.state['api_calls'])}")

    # Save final state
    project_state.save_state()
    print(f"\n💾 Project state saved to {project_state.state_file}")

    print("\n✅ Focused precaching completed!")
    print("\nBenefits:")
    print("• Core volumes (1-10) are now cached for all series")
    print("• Users will get instant results for the most commonly requested volumes")
    print("• Remaining volumes are cached for complete series coverage")


if __name__ == "__main__":
    main()