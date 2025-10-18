#!/usr/bin/env python3
"""
Test script to verify the text-based list display
"""

import os
import sys

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(__file__))

from rich.console import Console

from manga_lookup import BookInfo, display_text_list, show_book_details


def test_text_list_display():
    """Test if the text-based list displays correctly"""
    print("Testing text-based list display...")

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
            description="In modern-day Tokyo, shy college student Ken Kaneki's life changes forever when he becomes a half-ghoul after a fateful encounter.",
            physical_description="224 pages, 5 x 7.5 inches",
            genres=["Horror", "Dark Fantasy", "Seinen"],
            warnings=[],
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
            description="Monkey D. Luffy begins his journey to become the Pirate King by gathering a crew and searching for the legendary treasure One Piece.",
            physical_description="208 pages, 5 x 7.5 inches",
            genres=["Shonen", "Adventure", "Fantasy"],
            warnings=["MSRP $9.99 is below minimum $10 (rounded up to $10.0)"],
        ),
        BookInfo(
            series_name="Test Series",
            volume_number=1,
            book_title="Test Series (Volume 1)",
            authors=["Test, Author"],
            msrp_cost=None,
            isbn_13=None,
            publisher_name=None,
            copyright_year=None,
            description=None,
            physical_description=None,
            genres=[],
            warnings=["No MSRP found", "Could not extract valid copyright year"],
        ),
    ]

    console = Console()

    print("\nCalling display_text_list function...")
    try:
        # We'll simulate a quick test by calling the function but not waiting for input
        print("\n--- Text List Display Test ---")
        display_text_list(books, console)
        print("\n✓ Text list function executed successfully!")
        return True
    except Exception as e:
        print(f"\n✗ Error displaying text list: {e}")
        return False

def test_book_details():
    """Test the book details display"""
    print("\nTesting book details display...")

    book = BookInfo(
        series_name="Tokyo Ghoul",
        volume_number=1,
        book_title="Tokyo Ghoul (Volume 1)",
        authors=["Ishida, Sui"],
        msrp_cost=12.99,
        isbn_13="9781421580366",
        publisher_name="VIZ Media LLC",
        copyright_year=2015,
        description="In modern-day Tokyo, shy college student Ken Kaneki's life changes forever when he becomes a half-ghoul after a fateful encounter.",
        physical_description="224 pages, 5 x 7.5 inches",
        genres=["Horror", "Dark Fantasy", "Seinen"],
        warnings=[],
    )

    console = Console()

    try:
        print("\n--- Book Details Test ---")
        show_book_details(book, console)
        print("\n✓ Book details function executed successfully!")
        return True
    except Exception as e:
        print(f"\n✗ Error displaying book details: {e}")
        return False

if __name__ == "__main__":
    print("Running text-based list tests...\n")

    test1_passed = test_text_list_display()
    test2_passed = test_book_details()

    if test1_passed and test2_passed:
        print("\n✓ All text-based list tests passed!")
    else:
        print("\n✗ Some text-based list tests failed!")
