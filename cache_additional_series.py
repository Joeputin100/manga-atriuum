#!/usr/bin/env python3
"""
Cache Additional Manga Series

Precache data for additional requested manga series.
"""

import os
import sys
import time

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(__file__))

from manga_lookup import DeepSeekAPI, ProjectState, process_book_data

# Additional series with estimated volume counts
ADDITIONAL_SERIES = {
    "Noragami: Stray God": 26,
    "A Silent Voice": 7,
    "To Your Eternity": 21,
    "Golden Kamuy": 31,
    "Black Butler": 32,
    "Show-ha Shoten": 6,
    "Haikyuu!!": 45,
    "Blue Exorcist": 29,
    "One Punch Man": 28,
    "Mob Psycho 100": 16,
    "Attack on Titan": 34,
    "Attack on Titan: Before the Fall": 17,
    "Deadman Wonderland": 13,
    "Gantz Omnibus": 37,
    "Platinum End": 14,
    "Bakuman": 20,
    "Inuyashiki": 10,
    "Otherworldly Izakaya Nobu": 8,
    "Edens Zero": 30,
    "World Trigger": 25,
    "Flowers of Evil": 11,
    "Thermae Romae": 6,
    "Blood on the Tracks": 15,
    "Welcome Back Alice": 7,
    "Sue & Tai-chan": 4,
    "A Polar Bear in Love": 6,
    "Demon Slayer": 23,
    "Shaman King": 35,
    "Fairy Tail: 100 Year Quest": 15,
    "Beastars": 22,
    "Beast Complex": 6,
    "Children of Whales": 23,
    "Barefoot Gen": 10,
    "Banana Fish": 19,
    "Hunter x Hunter": 37,
    "Final Fantasy Lost Stranger": 6,
    "Thunder3": 4,
    "Scars": 3,
    "The Day Hikaru Died": 6,
    "Boys Run the Riot": 4,
    "Tokyo Revengers Full Color": 31,
    "Graineliers": 10,
    "Berserk Deluxe": 14,
    "Soul Eater": 25,
}


def precache_series_core_volumes(series_name: str, max_volumes: int, project_state: ProjectState, deepseek_api: DeepSeekAPI):
    """Precache core volumes (1-10) for a manga series"""
    print(f"\n📚 Precaching {series_name} (volumes 1-{min(10, max_volumes)})...")

    successful_volumes = 0
    failed_volumes = 0

    # Cache first 10 volumes or all volumes if less than 10
    end_volume = min(10, max_volumes)

    for volume in range(1, end_volume + 1):
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


def cache_series_names(series_names: list[str], project_state: ProjectState, deepseek_api: DeepSeekAPI):
    """Cache series name corrections for additional series"""
    print(f"\n🔍 Caching series name corrections for {len(series_names)} additional series...")

    successful = 0
    failed = 0

    for series_name in series_names:
        try:
            print(f"  {series_name}...", end=" ")

            # Get corrected series names
            suggestions = deepseek_api.correct_series_name(series_name)

            if suggestions and len(suggestions) > 0:
                print("✓")
                successful += 1
            else:
                print("✗ (no suggestions)")
                failed += 1

            # Add small delay to respect rate limits
            time.sleep(0.5)

        except Exception as e:
            print(f"✗ (error: {str(e)[:50]})")
            failed += 1
            continue

    return successful, failed


def main():
    """Main function to cache additional series"""
    print("🚀 Caching Additional Manga Series")
    print("=" * 60)
    print(f"Adding {len(ADDITIONAL_SERIES)} new series to cache...")
    print("=" * 60)

    # Initialize APIs
    try:
        deepseek_api = DeepSeekAPI()
        project_state = ProjectState()
    except Exception as e:
        print(f"❌ Failed to initialize APIs: {e}")
        return

    # Cache series names first
    series_names = list(ADDITIONAL_SERIES.keys())
    series_successful, series_failed = cache_series_names(series_names, project_state, deepseek_api)

    # Cache core volumes
    print("\n" + "=" * 60)
    print("Phase 2: Caching Core Volumes (1-10) for Additional Series...")
    print("=" * 60)

    total_successful = 0
    total_failed = 0

    for series_name, max_volumes in ADDITIONAL_SERIES.items():
        successful, failed = precache_series_core_volumes(series_name, max_volumes, project_state, deepseek_api)
        total_successful += successful
        total_failed += failed

    # Print summary
    print("\n" + "=" * 60)
    print("📊 Additional Series Caching Summary")
    print("=" * 60)
    print(f"Series processed: {len(ADDITIONAL_SERIES)}")
    print(f"Series names cached: {series_successful}")
    print(f"Core volumes cached: {total_successful}")
    print(f"Volumes failed/not found: {total_failed}")
    print(f"Total API calls made: {len(project_state.state['api_calls'])}")

    # Save final state
    project_state.save_state()
    print(f"\n💾 Project state saved to {project_state.state_file}")

    print("\n✅ Additional series caching completed!")
    print("\nBenefits:")
    print("• Additional series names cached for instant suggestions")
    print("• Core volumes (1-10) cached for all new series")
    print("• Expanded coverage for diverse manga preferences")


if __name__ == "__main__":
    main()
