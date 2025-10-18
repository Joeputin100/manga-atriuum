#!/usr/bin/env python3
"""
Add More Series to Database

This script adds Crayon Shin-chan, Sue and Tai-chan, Happiness, and Uzumaki.
"""

import time

# Import existing modules
from manga_lookup import DeepSeekAPI, GoogleBooksAPI, ProjectState, process_book_data


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

def add_series(series_name, max_volume):
    """Add a complete series to the database"""
    print(f"\n🎯 Adding {series_name} (1-{max_volume} volumes)")

    # Initialize APIs
    project_state = ProjectState()
    deepseek_api = DeepSeekAPI()
    google_api = GoogleBooksAPI()

    added_count = 0

    for volume in range(1, max_volume + 1):
        print(f"  Fetching {series_name} Volume {volume}...")

        # Get book data with retry
        book_data = get_book_data_with_retry(deepseek_api, series_name, volume, project_state)

        if book_data:
            # Process the data
            book = process_book_data(book_data, volume, google_api, project_state)

            if book:
                print(f"    ✓ Added {series_name} Vol. {volume}")
                added_count += 1
            else:
                print(f"    ✗ Failed to process {series_name} Vol. {volume}")
        else:
            print(f"    ✗ Failed to fetch {series_name} Vol. {volume}")

        # Rate limiting
        time.sleep(2)

    print(f"  ✅ Completed {series_name}: {added_count}/{max_volume} volumes added")
    return added_count

def main():
    """Add the requested series"""
    print("🚀 Adding Requested Series to Database")
    print("=" * 60)

    # Series to add with their approximate volume counts
    requested_series = [
        ("Crayon Shin-chan", 60),  # Very long-running, conservative estimate
        ("Sue and Tai-chan", 15),  # Approximate
        ("Happiness", 50),
        ("Uzumaki", 3),  # Complete series
    ]

    total_added = 0

    for series_name, max_vol in requested_series:
        added = add_series(series_name, max_vol)
        total_added += added

    print(f"\n🎉 Total: Added {total_added} volumes across {len(requested_series)} series!")
    print("Enjoy these additional manga series!")

if __name__ == "__main__":
    main()
