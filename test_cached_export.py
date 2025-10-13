#!/usr/bin/env python3
"""
Test MARC Export with Cached Data

Test exporting MARC records using the currently cached manga data.
"""

import sys
import os

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(__file__))

from manga_lookup import DeepSeekAPI, ProjectState, process_book_data
from marc_exporter import export_books_to_marc


def test_cached_export():
    """Test exporting MARC records from cached data"""
    print("🧪 Testing MARC Export with Cached Data")
    print("=" * 60)

    # Initialize APIs
    try:
        deepseek_api = DeepSeekAPI()
        project_state = ProjectState()
    except Exception as e:
        print(f"❌ Failed to initialize APIs: {e}")
        return

    # Test with a few cached series
    test_series = [
        "Tokyo Ghoul",
        "Death Note",
        "A Silent Voice"
    ]

    all_books = []

    for series_name in test_series:
        print(f"\n📚 Processing {series_name}...")

        # Try to get volumes 1-3
        for volume in range(1, 4):
            try:
                prompt = deepseek_api._create_comprehensive_prompt(series_name, volume)
                cached_response = project_state.get_cached_response(prompt, volume)

                if cached_response:
                    print(f"  Volume {volume}... ✓ (cached)")

                    # Parse cached data
                    book_data = None
                    try:
                        book_data = json.loads(cached_response)
                    except:
                        # Try to extract JSON from response
                        import re
                        json_match = re.search(r'\{.*\}', cached_response, re.DOTALL)
                        if json_match:
                            book_data = json.loads(json_match.group())

                    if book_data:
                        book = process_book_data(book_data, volume)
                        all_books.append(book)
                        print(f"    Title: {book.book_title}")
                        print(f"    Author: {', '.join(book.authors)}")
                else:
                    print(f"  Volume {volume}... ✗ (not cached)")

            except Exception as e:
                print(f"  Volume {volume}... ✗ (error: {str(e)[:50]})")

    # Export to MARC if we have books
    if all_books:
        print(f"\n📁 Exporting {len(all_books)} books to MARC format...")

        output_file = "cached_manga_test.mrc"
        export_books_to_marc(all_books, output_file, "C")

        print(f"✅ MARC export completed: {output_file}")
        print("\n📊 Export Summary:")
        for book in all_books:
            print(f"  • {book.series_name} Vol.{book.volume_number}: {book.book_title}")
    else:
        print("\n❌ No cached books found for export")


if __name__ == "__main__":
    import json
    test_cached_export()