#!/usr/bin/env python3
"""
Simple test script to verify Rich table creation without interactive mode
"""

import os
import sys

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(__file__))

from rich.console import Console
from rich.table import Table

from manga_lookup import BookInfo


def test_table_creation():
    """Test if the Rich table can be created and displayed"""
    print("Testing Rich table creation...")

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
            warnings=[],
        ),
    ]

    console = Console()

    # Test basic table creation (similar to display_rich_table but without interactive loop)
    table = Table(title=f"Manga Series Results ({len(books)} books found)", show_header=True, header_style="bold magenta")

    # Add columns
    table.add_column("#", style="dim", width=4)
    table.add_column("Volume", style="cyan", width=8)
    table.add_column("Title", style="white", width=25)
    table.add_column("Authors", style="yellow", width=20)
    table.add_column("MSRP", style="green", width=8)
    table.add_column("ISBN-13", style="blue", width=15)
    table.add_column("Publisher", style="magenta", width=20)
    table.add_column("Year", style="cyan", width=6)
    table.add_column("Description", style="dim", width=30)
    table.add_column("Physical", style="dim", width=20)
    table.add_column("Genres", style="yellow", width=20)

    # Add rows
    for i, book in enumerate(books, 1):
        # Truncate long text fields for display
        title = book.book_title[:22] + "..." if len(book.book_title) > 25 else book.book_title
        from manga_lookup import DataValidator
        authors = DataValidator.format_authors_list(book.authors)
        authors = authors[:17] + "..." if len(authors) > 20 else authors
        isbn = book.isbn_13[:12] + "..." if book.isbn_13 and len(book.isbn_13) > 15 else (book.isbn_13 or "Unknown")
        publisher = book.publisher_name[:17] + "..." if book.publisher_name and len(book.publisher_name) > 20 else (book.publisher_name or "Unknown")
        year = str(book.copyright_year) if book.copyright_year else "Unknown"
        description = book.description[:27] + "..." if book.description and len(book.description) > 30 else (book.description or "")
        physical = book.physical_description[:17] + "..." if book.physical_description and len(book.physical_description) > 20 else (book.physical_description or "")
        genres = ", ".join(book.genres[:2])[:17] + "..." if book.genres and len(", ".join(book.genres)) > 20 else ", ".join(book.genres) if book.genres else ""
        msrp = f"${book.msrp_cost:.2f}" if book.msrp_cost else "Unknown"

        table.add_row(
            str(i),
            str(book.volume_number),
            title,
            authors,
            msrp,
            isbn,
            publisher,
            year,
            description,
            physical,
            genres,
        )

    # Display the table
    console.print(table)
    print("\n✓ Rich table created and displayed successfully!")
    return True

def test_author_formatting_in_table():
    """Test that author formatting works correctly in the table context"""
    print("\nTesting author formatting in table context...")

    # Test various author formats
    test_cases = [
        (["Ishida, Sui"], "Ishida, Sui"),
        (["Oda, Eiichiro"], "Oda, Eiichiro"),
        (["Kishimoto, Masashi"], "Kishimoto, Masashi"),
        ([], ""),
        (["Oda"], "Oda"),
    ]

    from manga_lookup import DataValidator

    all_passed = True
    for input_authors, expected in test_cases:
        result = DataValidator.format_authors_list(input_authors)
        if result == expected:
            print(f"  ✓ {input_authors} -> '{result}'")
        else:
            print(f"  ✗ {input_authors} -> '{result}' (expected: '{expected}')")
            all_passed = False

    return all_passed

if __name__ == "__main__":
    print("Running Rich table creation tests...\n")

    test1_passed = test_table_creation()
    test2_passed = test_author_formatting_in_table()

    if test1_passed and test2_passed:
        print("\n✓ All Rich table tests passed!")
    else:
        print("\n✗ Some Rich table tests failed!")
