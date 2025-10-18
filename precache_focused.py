#!/usr/bin/env python3
"""
Focused Manga Series Precaching

Precaches data for the most popular manga series first.
"""

import os
import sys
import time

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(__file__))

from manga_lookup import DeepSeekAPI, ProjectState, process_book_data

# Focus on most popular series with fewer volumes first
FOCUSED_SERIES = {
    "Tokyo Ghoul": 5,           # 5 volumes
    "Tokyo Ghoul:re": 5,        # 5 volumes
    "Death Note": 5,            # 5 volumes
    "A Silent Voice": 5,        # 5 volumes
    "Assassination Classroom": 5,  # 5 volumes
    "Cells At Work": 5,         # 5 volumes
    "Akira": 5,                 # 5 volumes
    "Noragami: Stray God": 5,   # 5 volumes
    "Tegami Bachi": 5,          # 5 volumes
    "Children of Whales": 5,    # 5 volumes
}


def check_existing_cache(series_name: str, max_volumes: int, deepseek_api: DeepSeekAPI, project_state: ProjectState) -> list[int]:
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


def precache_missing_volumes(series_name: str, missing_volumes: list[int], deepseek_api: DeepSeekAPI, project_state: ProjectState) -> dict[str, int]:
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

                # Show brief info
                print(f"      Title: {book.book_title}")
                print(f"      Author: {', '.join(book.authors)}")

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
    """Main function to precache focused series"""
    print("🎯 Focused Manga Series Precaching")
    print("=" * 60)

    # Initialize APIs
    try:
        deepseek_api = DeepSeekAPI()
        project_state = ProjectState()
    except Exception as e:
        print(f"❌ Failed to initialize APIs: {e}")
        return

    total_series = len(FOCUSED_SERIES)
    total_cached = 0
    total_fetched = 0
    total_failed = 0

    print(f"Analyzing cache for {total_series} focused manga series...")
    print("=" * 60)

    # Process each series
    for series_name, max_volumes in FOCUSED_SERIES.items():
        print(f"\n📚 {series_name} (volumes 1-{max_volumes})")

        # Check existing cache
        cached_volumes, missing_volumes = check_existing_cache(series_name, max_volumes, deepseek_api, project_state)

        print(f"  Cached: {len(cached_volumes)} volumes")
        print(f"  Missing: {len(missing_volumes)} volumes")

        total_cached += len(cached_volumes)

        # Precache missing volumes
        if missing_volumes:
            print("  Precaching missing volumes...")
            results = precache_missing_volumes(series_name, missing_volumes, deepseek_api, project_state)
            total_fetched += results["successful"]
            total_failed += results["failed"]
        else:
            print("  ✓ All volumes already cached")

    # Print summary
    print("\n" + "=" * 60)
    print("📊 Focused Precaching Summary")
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

    print("\n✅ Focused precaching completed!")
    print("\nThe cache now contains data for:")
    for series_name in FOCUSED_SERIES:
        print(f"  • {series_name}")


if __name__ == "__main__":
    main()
