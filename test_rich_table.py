#!/usr/bin/env python3
"""
Test script to check if the Rich table display is working correctly
"""

import sys
import os

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(__file__))

from manga_lookup import BookInfo, display_rich_table
from rich.console import Console

def test_rich_table_display():
    """Test if the Rich table displays correctly"""
    print("Testing Rich table display...")

    # Create sample book data
    books = [
        BookInfo(
            series_name="Tokyo Ghoul",
            volume_number=1,
            book_title="Tokyo Ghoul (Volume 1)",
            authors=["Ishida, Sui"],
            msrp_cost=12.99,
            isbn_13="9781421580366",
            publisher_name="VIZ Media LLC",
            copyright_year=2015,
            description="In modern-day Tokyo, shy college student Ken Kaneki's life changes forever...",
            physical_description="224 pages, 5 x 7.5 inches",
            genres=["Horror", "Dark Fantasy", "Seinen"],
            warnings=[]
        ),
        BookInfo(
            series_name="One Piece",
            volume_number=1,
            book_title="One Piece (Volume 1)",
            authors=["Oda, Eiichiro"],
            msrp_cost=9.99,
            isbn_13="9781569319017",
            publisher_name="VIZ Media LLC",
            copyright_year=2003,
            description="Monkey D. Luffy begins his journey to become the Pirate King...",
            physical_description="208 pages, 5 x 7.5 inches",
            genres=["Shonen", "Adventure", "Fantasy"],
            warnings=[]
        )
    ]

    console = Console()

    print("\nCalling display_rich_table function...")
    try:
        display_rich_table(books, console)
        print("\n✓ Rich table function executed successfully!")
        return True
    except Exception as e:
        print(f"\n✗ Error displaying Rich table: {e}")
        return False

def test_table_with_empty_data():
    """Test table display with edge cases"""
    print("\nTesting Rich table with edge cases...")

    # Test with empty books list
    console = Console()

    try:
        display_rich_table([], console)
        print("✓ Empty table handled successfully!")
    except Exception as e:
        print(f"✗ Error with empty table: {e}")
        return False

    # Test with book that has missing data
    books_with_missing_data = [
        BookInfo(
            series_name="Test Series",
            volume_number=1,
            book_title="Test Series (Volume 1)",
            authors=[],  # Empty authors
            msrp_cost=None,  # No MSRP
            isbn_13=None,  # No ISBN
            publisher_name=None,  # No publisher
            copyright_year=None,  # No year
            description=None,  # No description
            physical_description=None,  # No physical description
            genres=[],  # No genres
            warnings=["No MSRP found", "Could not extract valid copyright year"]
        )
    ]

    try:
        display_rich_table(books_with_missing_data, console)
        print("✓ Table with missing data handled successfully!")
        return True
    except Exception as e:
        print(f"✗ Error with missing data table: {e}")
        return False

if __name__ == "__main__":
    print("Running Rich table tests...\n")

    test1_passed = test_rich_table_display()
    test2_passed = test_table_with_empty_data()

    if test1_passed and test2_passed:
        print("\n✓ All Rich table tests passed!")
    else:
        print("\n✗ Some Rich table tests failed!")