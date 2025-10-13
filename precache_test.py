#!/usr/bin/env python3
"""
Test Precaching - Cache a few series first
"""

import sys
import os
import time

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(__file__))

from manga_lookup import DeepSeekAPI, ProjectState, process_book_data


# Test with smaller series first
TEST_SERIES = {
    "Tokyo Ghoul": 3,  # First 3 volumes
    "Death Note": 3,   # First 3 volumes
    "A Silent Voice": 3,  # First 3 volumes
}


def main():
    print("🧪 Testing Manga Series Precaching")
    print("=" * 50)

    # Initialize APIs
    try:
        deepseek_api = DeepSeekAPI()
        project_state = ProjectState()
    except Exception as e:
        print(f"❌ Failed to initialize APIs: {e}")
        return

    total_successful = 0
    total_failed = 0

    for series_name, max_volumes in TEST_SERIES.items():
        print(f"\n📚 Precaching {series_name} (volumes 1-{max_volumes})...")

        for volume in range(1, max_volumes + 1):
            try:
                print(f"  Volume {volume}...", end=" ")

                # Check if already cached
                prompt = deepseek_api._create_comprehensive_prompt(series_name, volume)
                cached_response = project_state.get_cached_response(prompt, volume)

                if cached_response:
                    print("✓ (cached)")
                    total_successful += 1
                    continue

                # Fetch fresh data
                book_data = deepseek_api.get_book_info(series_name, volume, project_state)

                if book_data:
                    book = process_book_data(book_data, volume)
                    print("✓")
                    total_successful += 1

                    # Show some book info
                    print(f"    Title: {book.book_title}")
                    print(f"    Author: {', '.join(book.authors)}")
                    print(f"    ISBN: {book.isbn_13}")

                    # Add delay to respect rate limits
                    time.sleep(1)
                else:
                    print("✗ (not found)")
                    total_failed += 1

            except Exception as e:
                print(f"✗ (error: {str(e)[:50]})")
                total_failed += 1
                continue

    # Print summary
    print("\n" + "=" * 50)
    print("📊 Test Precaching Summary")
    print("=" * 50)
    print(f"Series processed: {len(TEST_SERIES)}")
    print(f"Volumes successfully cached: {total_successful}")
    print(f"Volumes failed/not found: {total_failed}")
    print(f"Total API calls made: {len(project_state.state['api_calls'])}")

    # Save final state
    project_state.save_state()
    print(f"\n💾 Project state saved to {project_state.state_file}")

    print("\n✅ Test precaching completed!")


if __name__ == "__main__":
    main()