#!/usr/bin/env python3
"""
Test script to reproduce the author parsing issue from API data
"""

import os
import sys

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(__file__))

from manga_lookup import DataValidator, process_book_data


def test_author_parsing_from_api():
    """Test how authors are parsed from API data"""
    print("Testing author parsing from API data...")

    # Simulate API responses that might cause trailing comma issues
    test_cases = [
        # Case 1: Single author already formatted
        {
            "series_name": "One Piece",
            "volume_number": 1,
            "book_title": "One Piece (Volume 1)",
            "authors": "Oda, Eiichiro",  # String with comma
            "msrp_cost": 9.99,
            "isbn_13": "9781569319017",
            "publisher_name": "VIZ Media LLC",
            "copyright_year": 2003,
            "description": "Monkey D. Luffy begins his journey...",
            "physical_description": "208 pages, 5 x 7.5 inches",
            "genres": ["Shonen", "Adventure", "Fantasy"],
        },
        # Case 2: Multiple authors as string
        {
            "series_name": "Naruto",
            "volume_number": 1,
            "book_title": "Naruto (Volume 1)",
            "authors": "Kishimoto, Masashi, Some Other Author",  # Multiple authors as string
            "msrp_cost": 9.99,
            "isbn_13": "9781421536252",
            "publisher_name": "VIZ Media LLC",
            "copyright_year": 2003,
            "description": "Naruto Uzumaki begins his journey...",
            "physical_description": "192 pages, 5 x 7.5 inches",
            "genres": ["Shonen", "Action", "Fantasy"],
        },
        # Case 3: Authors as list (ideal case)
        {
            "series_name": "Bleach",
            "volume_number": 1,
            "book_title": "Bleach (Volume 1)",
            "authors": ["Kubo, Tite"],  # List format
            "msrp_cost": 9.99,
            "isbn_13": "9781591164418",
            "publisher_name": "VIZ Media LLC",
            "copyright_year": 2004,
            "description": "Ichigo Kurosaki becomes a Soul Reaper...",
            "physical_description": "200 pages, 5 x 7.5 inches",
            "genres": ["Shonen", "Supernatural", "Action"],
        },
        # Case 4: Single author without comma
        {
            "series_name": "Attack on Titan",
            "volume_number": 1,
            "book_title": "Attack on Titan (Volume 1)",
            "authors": "Isayama Hajime",  # String without comma
            "msrp_cost": 10.99,
            "isbn_13": "9781612620244",
            "publisher_name": "Kodansha Comics",
            "copyright_year": 2012,
            "description": "Humanity fights against giant Titans...",
            "physical_description": "192 pages, 5 x 7.5 inches",
            "genres": ["Dark Fantasy", "Action", "Horror"],
        },
    ]

    for i, raw_data in enumerate(test_cases, 1):
        print(f"\nTest Case {i}:")
        print(f"  Input authors: {raw_data.get('authors')}")
        print(f"  Input type: {type(raw_data.get('authors'))}")

        book = process_book_data(raw_data, raw_data["volume_number"])

        print(f"  Processed authors: {book.authors}")
        formatted_authors = DataValidator.format_authors_list(book.authors)
        print(f"  Formatted authors: '{formatted_authors}'")

        # Check for trailing comma issues
        if formatted_authors.endswith(","):
            print("  ⚠️  WARNING: Trailing comma detected!")

        if len(book.authors) == 1 and "," in formatted_authors and formatted_authors.count(",") > 1:
            print("  ⚠️  WARNING: Multiple commas in single author!")

if __name__ == "__main__":
    print("Running author parsing tests...\n")
    test_author_parsing_from_api()
