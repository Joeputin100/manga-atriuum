#!/usr/bin/env python3
"""
Precache Manga Series Data

Precaches data for all extant English language paperback volumes of popular manga series
for faster lookup and MARC export operations.
"""

import os
import sys
import time

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
    "Haikyu!!": 45,
}


def precache_series(series_name: str, max_volumes: int, project_state: ProjectState, deepseek_api: DeepSeekAPI):
    """Precache data for a single manga series"""
    print(f"\n📚 Precaching {series_name} (volumes 1-{max_volumes})...")

    successful_volumes = 0
    failed_volumes = 0

    for volume in range(1, max_volumes + 1):
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

            # Continue with next volume on error
            continue

    return successful_volumes, failed_volumes


def main():
    """Main function to precache all series"""
    print("🚀 Starting Manga Series Precaching")
    print("=" * 60)

    # Initialize APIs
    try:
        deepseek_api = DeepSeekAPI()
        project_state = ProjectState()
    except Exception as e:
        print(f"❌ Failed to initialize APIs: {e}")
        return

    total_series = len(SERIES_TO_PRECACHE)
    total_successful = 0
    total_failed = 0

    print(f"Precaching {total_series} manga series...")
    print("=" * 60)

    # Precache each series
    for series_name, max_volumes in SERIES_TO_PRECACHE.items():
        successful, failed = precache_series(series_name, max_volumes, project_state, deepseek_api)
        total_successful += successful
        total_failed += failed

    # Print summary
    print("\n" + "=" * 60)
    print("📊 Precaching Summary")
    print("=" * 60)
    print(f"Series processed: {total_series}")
    print(f"Volumes successfully cached: {total_successful}")
    print(f"Volumes failed/not found: {total_failed}")
    print(f"Total API calls made: {len(project_state.state['api_calls'])}")

    # Save final state
    project_state.save_state()
    print(f"\n💾 Project state saved to {project_state.state_file}")

    print("\n✅ Precaching completed!")
    print("\nNext steps:")
    print("1. Use manga_lookup.py to search for specific volumes")
    print("2. Export to MARC format using the 'm' option")
    print("3. Check project_state.json for cached data")


if __name__ == "__main__":
    main()
