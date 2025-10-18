#!/usr/bin/env python3
"""
Cache Requested Manga Series

Precaches data for all extant English language paperback volumes of the requested manga series
for faster lookup and MARC export operations.
"""

import os
import sys
import time

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(__file__))

from manga_lookup import DeepSeekAPI, ProjectState, process_book_data

# Requested series with estimated volume counts
REQUESTED_SERIES = {
    "Naruto": 72,
    "Boruto: Two Blue Vortex": 5,
    "Boruto: Naruto The Next Generation": 20,
    "Bleach": 74,
    "One Piece": 105,
    "Black Clover": 35,
    "Tokyo Ghoul": 14,
    "Tokyo Ghoul:re": 16,
    "Assassination Classroom": 21,
    "Akira": 6,
    "My Hero Academia": 40,
    "Fairy Tail": 63,
    "Attack on Titan": 34,
    "Tegami Bachi": 20,
    "Magus of the Library": 7,
    "Chainsaw Man": 15,
    "Dragon Ball Z": 26,
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

                # Show some book info
                print(f"    Title: {book.book_title}")
                print(f"    Author: {', '.join(book.authors)}")
                print(f"    ISBN: {book.isbn_13}")

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
    """Main function to precache all requested series"""
    print("🚀 Starting Manga Series Precaching")
    print("=" * 60)
    print("Caching the following series:")
    for series_name, max_volumes in REQUESTED_SERIES.items():
        print(f"  • {series_name} (volumes 1-{max_volumes})")
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

    print(f"\nPrecaching {total_series} manga series...")
    print("=" * 60)

    # Precache each series
    for series_name, max_volumes in REQUESTED_SERIES.items():
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
