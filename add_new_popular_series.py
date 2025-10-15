#!/usr/bin/env python3
"""
Add 10 New Popular Shonen Manga Series to Database

This script adds volumes for 10 currently popular shonen manga series
that are not yet in the database.
"""

import os
import json
import time
from typing import List, Dict

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

def main():
    """Add 10 new popular shonen manga series"""
    print("🚀 Adding 10 New Popular Shonen Manga Series to Database")
    print("=" * 60)

    # Initialize APIs
    project_state = ProjectState()
    deepseek_api = DeepSeekAPI()
    google_api = GoogleBooksAPI()

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

    total_added = 0

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
                    # Save incrementally
                    with open('project_state.json', 'w') as f:
                        json.dump(project_state, f, indent=2)
                else:
                    print(f"    ✗ Failed to process {series_name} Vol. {volume}")
            else:
                print(f"    ✗ Failed to fetch {series_name} Vol. {volume}")

            # Rate limiting
            time.sleep(2)

        print(f"  ✅ Completed {series_name}: {series_added}/{max_vol} volumes added")

    print(f"\n🎉 Grand Total: Added {total_added} volumes across 10 new series!")
    print("Your database now includes the most popular current shonen manga!")

if __name__ == "__main__":
    main()