#!/usr/bin/env python3
"""
Integration test to check if there are any actual trailing comma issues
"""

import os
import sys

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(__file__))

from manga_lookup import DataValidator, process_book_data


def test_with_real_api_data():
    """Test with actual API response data from project_state.json"""
    print("Testing with real API response data...")

    # Simulate the actual API response format from the cached data
    test_data = [
        {
            "series_name": "Tokyo Ghoul",
            "volume_number": 1,
            "book_title": "Tokyo Ghoul (Volume 1)",
            "authors": ["Ishida, Sui"],  # List format from API
            "msrp_cost": 12.99,
            "isbn_13": "9781421580366",
            "publisher_name": "VIZ Media LLC",
            "copyright_year": 2015,
            "description": "In modern-day Tokyo, shy college student Ken Kaneki's life changes forever...",
            "physical_description": "224 pages, 5 x 7.5 inches, black and white illustrations",
            "genres": ["Horror", "Dark Fantasy", "Seinen", "Supernatural", "Psychological"],
        },
        {
            "series_name": "One Piece",
            "volume_number": 1,
            "book_title": "One Piece (Volume 1)",
            "authors": ["Oda, Eiichiro"],  # List format from API
            "msrp_cost": 9.99,
            "isbn_13": "9781569319017",
            "publisher_name": "VIZ Media LLC",
            "copyright_year": 2003,
            "description": "Monkey D. Luffy begins his journey...",
            "physical_description": "208 pages, 5 x 7.5 inches",
            "genres": ["Shonen", "Adventure", "Fantasy"],
        },
    ]

    all_passed = True
    for i, raw_data in enumerate(test_data, 1):
        print(f"\nTest Case {i}:")
        print(f"  Input authors: {raw_data.get('authors')}")

        book = process_book_data(raw_data, raw_data["volume_number"])

        print(f"  Processed authors: {book.authors}")
        formatted_authors = DataValidator.format_authors_list(book.authors)
        print(f"  Formatted authors: '{formatted_authors}'")

        # Check for trailing comma issues
        if formatted_authors.endswith(","):
            print("  ⚠️  WARNING: Trailing comma detected!")
            all_passed = False

        # Check for multiple commas in single author
        if len(book.authors) == 1 and "," in formatted_authors and formatted_authors.count(",") > 1:
            print("  ⚠️  WARNING: Multiple commas in single author!")
            all_passed = False

        # Check if the formatting is correct
        expected_formats = {
            1: "Ishida, Sui",
            2: "Oda, Eiichiro",
        }
        if formatted_authors != expected_formats[i]:
            print(f"  ⚠️  WARNING: Unexpected format! Expected: '{expected_formats[i]}'")
            all_passed = False

    return all_passed

def test_edge_cases():
    """Test edge cases that might cause trailing comma issues"""
    print("\nTesting edge cases...")

    edge_cases = [
        # Case where API might return string instead of list
        {
            "series_name": "Test Series",
            "volume_number": 1,
            "book_title": "Test Series (Volume 1)",
            "authors": "Oda, Eiichiro",  # String instead of list
            "msrp_cost": 9.99,
            "isbn_13": "9781234567890",
            "publisher_name": "Test Publisher",
            "copyright_year": 2023,
            "description": "Test description",
            "physical_description": "200 pages",
            "genres": ["Test"],
        },
        # Case with multiple authors as string
        {
            "series_name": "Test Series",
            "volume_number": 1,
            "book_title": "Test Series (Volume 1)",
            "authors": "Oda, Eiichiro, Kishimoto, Masashi",  # Multiple authors as string
            "msrp_cost": 9.99,
            "isbn_13": "9781234567890",
            "publisher_name": "Test Publisher",
            "copyright_year": 2023,
            "description": "Test description",
            "physical_description": "200 pages",
            "genres": ["Test"],
        },
    ]

    all_passed = True
    for i, raw_data in enumerate(edge_cases, 1):
        print(f"\nEdge Case {i}:")
        print(f"  Input authors: {raw_data.get('authors')}")
        print(f"  Input type: {type(raw_data.get('authors'))}")

        book = process_book_data(raw_data, raw_data["volume_number"])

        print(f"  Processed authors: {book.authors}")
        formatted_authors = DataValidator.format_authors_list(book.authors)
        print(f"  Formatted authors: '{formatted_authors}'")

        # Check for trailing comma issues
        if formatted_authors.endswith(","):
            print("  ⚠️  WARNING: Trailing comma detected!")
            all_passed = False

    return all_passed

if __name__ == "__main__":
    print("Running integration tests...\n")

    test1_passed = test_with_real_api_data()
    test2_passed = test_edge_cases()

    if test1_passed and test2_passed:
        print("\n✓ All integration tests passed!")
    else:
        print("\n✗ Some integration tests failed!")
