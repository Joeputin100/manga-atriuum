#!/usr/bin/env python3
"""
Add 10 New Popular Shonen Manga Series

Adds all volumes of 10 currently popular shonen manga series to expand the database.
Commits and pushes after every 10 volumes.
"""

import os
import json
import time
import subprocess

# Import existing modules
from manga_lookup import DeepSeekAPI, DataValidator, GoogleBooksAPI, process_book_data, ProjectState

def get_book_data_with_retry(api, series, volume, project_state, max_retries=3):
    """Get book data with retry logic for network errors"""
    for attempt in range(max_retries):
        try:
            return api.get_book_info(series, volume, project_state)
        except Exception as e:
            if ("SSL" in str(e) or "Max retries exceeded" in str(e)) and attempt < max_retries - 1:
                print(f"    Network error, retrying in 5 seconds... (attempt {attempt + 1}/{max_retries})")
                time.sleep(5)
            else:
                print(f"    Failed after {max_retries} attempts: {e}")
                return None
    return None

def commit_and_push(count):
    """Commit and push changes after every 10 volumes"""
    try:
        subprocess.run(['git', 'add', 'project_state.json'], check=True)
        subprocess.run(['git', 'commit', '-m', f'feat: add {count} volumes from new shonen series'], check=True)
        subprocess.run(['git', 'push', 'origin', 'main'], check=True)
        print(f"✓ Committed and pushed after {count} volumes")
    except subprocess.CalledProcessError as e:
        print(f"✗ Git operation failed: {e}")

def main():
    """Add 10 new popular shonen manga series"""
    print("🚀 Adding 10 New Popular Shonen Manga Series to Database")
    print("=" * 60)

    # 10 popular shonen manga series with their max volumes
    new_series = {
        'Demon Slayer: Kimetsu no Yaiba': 23,
        'Jujutsu Kaisen': 23,
        'My Hero Academia': 38,
        'Chainsaw Man': 15,
        'Spy x Family': 11,
        'Dr. Stone': 26,
        'Fire Force': 34,
        'The Rising of the Shield Hero': 45,
        'Crayon Shin-chan': 60,
        'Happiness': 50,
    }

    # Initialize APIs
    project_state = ProjectState()
    deepseek_api = DeepSeekAPI()
    google_api = GoogleBooksAPI()

    total_added = 0
    commit_count = 0

    for series_name, max_vol in new_series.items():
        print(f"\n🎯 Adding {series_name} (1-{max_vol} volumes)")

        series_added = 0

        for volume in range(1, max_vol + 1):
            print(f"  Fetching {series_name} Volume {volume}...")

            # Get book info with retry
            book_data = get_book_data_with_retry(deepseek_api, series_name, volume, project_state)

            if book_data:
                # Process the data
                book = process_book_data(book_data, volume, google_api, project_state)

                if book:
                    print(f"    ✓ Added {series_name} Vol. {volume}")
                    series_added += 1
                    total_added += 1
                    commit_count += 1

                    # Save incrementally
                    with open('project_state.json', 'w') as f:
                    state_dict = {
                        'api_calls': getattr(project_state, 'api_calls', []),
                        'cached_responses': getattr(project_state, 'cached_responses', {}),
                        'start_time': getattr(project_state, 'start_time', None),
                        'interactions': getattr(project_state, 'interactions', [])
                    }
                    with open('project_state.json', 'w') as f:
                        json.dump(state_dict, f, indent=2)

                    # Commit and push every 10 volumes
                    if commit_count >= 10:
                        commit_and_push(total_added)
                        commit_count = 0
                else:
                    print(f"    ✗ Failed to process {series_name} Vol. {volume}")
            else:
                print(f"    ✗ Failed to fetch {series_name} Vol. {volume}")

            # Rate limiting
            time.sleep(2)

        print(f"  ✅ Completed {series_name}: {series_added}/{max_vol} volumes added")

    # Final commit if any remaining
    if commit_count > 0:
        commit_and_push(total_added)

    print(f"\n🎉 Grand Total: Added {total_added} volumes across 10 new series!")

if __name__ == "__main__":
    main()