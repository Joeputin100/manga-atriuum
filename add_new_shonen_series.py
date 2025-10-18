#!/usr/bin/env python3
"""
Add 10 New Popular Shonen Manga Series to Database

This script adds all volumes of 10 currently popular shonen manga series
not yet in the database.
"""

import json
import time

# Import existing modules
from manga_lookup import DeepSeekAPI, GoogleBooksAPI, ProjectState, process_book_data


def main():
    """Add new shonen series"""
    print("🚀 Adding 10 New Popular Shonen Manga Series to Database")
    print("=" * 60)

    # 10 popular shonen manga series not in db
    new_series = [
        ("Demon Slayer: Kimetsu no Yaiba", 23),
        ("Jujutsu Kaisen", 23),
        ("My Hero Academia", 38),
        ("Chainsaw Man", 15),
        ("Spy x Family", 11),
        ("Dr. Stone", 26),
        ("Fire Force", 34),
        ("The Rising of the Shield Hero", 45),
        ("Crayon Shin-chan", 60),
        ("Happiness", 50),
    ]

    # Initialize APIs
    project_state = ProjectState()
    deepseek_api = DeepSeekAPI()
    google_api = GoogleBooksAPI()

    total_added = 0

    for series_name, max_volumes in new_series:
        print(f"\n🎯 Adding {series_name} (1-{max_volumes} volumes)")

        series_added = 0

        for volume in range(1, max_volumes + 1):
            print(f"  Fetching {series_name} Volume {volume}...")

            # Get book info
            book_data = deepseek_api.get_book_info(series_name, volume, project_state)

            if book_data:
                # Process the data
                book = process_book_data(book_data, volume, google_api, project_state)

                if book:
                    print(f"    ✓ Added {series_name} Vol. {volume}")
                    series_added += 1
                    total_added += 1
                    # Save incrementally
                    with open("project_state.json", "w") as f:
                        json.dump(project_state, f, indent=2)
                else:
                    print(f"    ✗ Failed to process {series_name} Vol. {volume}")
            else:
                print(f"    ✗ Failed to fetch {series_name} Vol. {volume}")

            # Rate limiting
            time.sleep(2)

        print(f"  ✅ Completed {series_name}: {series_added}/{max_volumes} volumes added")

    print(f"\n🎉 Grand Total: Added {total_added} volumes across {len(new_series)} new series!")

if __name__ == "__main__":
    main()
