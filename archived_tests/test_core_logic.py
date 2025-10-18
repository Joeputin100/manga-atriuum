#!/usr/bin/env python3
"""
Test Core Logic - Development Workflow

This script allows testing the manga lookup core logic without Streamlit.
Use this for development and testing on Termux.
"""

import os

# Import existing core logic
from manga_lookup import (
    BookInfo,
    DataValidator,
    DeepSeekAPI,
    ProjectState,
    generate_sequential_barcodes,
    parse_volume_range,
    process_book_data,
)

# Import MARC exporter
from marc_exporter import export_books_to_marc


def test_volume_parsing():
    """Test volume range parsing"""
    print("🔍 Testing Volume Range Parsing...")

    test_cases = [
        ("1-5", [1, 2, 3, 4, 5]),
        ("17-18-19", [17, 18, 19]),
        ("1-5,7,10", [1, 2, 3, 4, 5, 7, 10]),
        ("17-18-19,20-21-22", [17, 18, 19, 20, 21, 22]),
    ]

    for input_str, expected in test_cases:
        result = parse_volume_range(input_str)
        status = "✓" if result == expected else "✗"
        print(f"  {status} '{input_str}' -> {result}")

    print()


def test_barcode_generation():
    """Test barcode generation"""
    print("🏷️ Testing Barcode Generation...")

    test_cases = [
        ("T000001", 3, ["T000001", "T000002", "T000003"]),
        ("MANGA001", 2, ["MANGA001", "MANGA002"]),
    ]

    for start_barcode, count, expected in test_cases:
        result = generate_sequential_barcodes(start_barcode, count)
        status = "✓" if result == expected else "✗"
        print(f"  {status} Start: '{start_barcode}', Count: {count} -> {result}")

    print()


def test_api_connection():
    """Test DeepSeek API connection"""
    print("🌐 Testing API Connection...")

    try:
        # Check if API key is available
        api_key = os.getenv("DEEPSEEK_API_KEY")
        if not api_key:
            print("  ⚠️ DEEPSEEK_API_KEY not found in environment")
            print("  Set it with: export DEEPSEEK_API_KEY='your_key_here'")
            return False

        # Test API initialization
        api = DeepSeekAPI()
        print("  ✓ API initialized successfully")

        # Test series name correction
        print("  Testing series name correction...")
        suggestions = api.correct_series_name("One Piece")
        print(f"  ✓ Got {len(suggestions)} suggestions: {suggestions[:2]}...")

        return True

    except Exception as e:
        print(f"  ✗ API Error: {e}")
        return False


def test_single_lookup():
    """Test a single manga lookup"""
    print("📚 Testing Single Manga Lookup...")

    try:
        api = DeepSeekAPI()
        project_state = ProjectState()

        # Test with a known series
        series_name = "One Piece"
        volume = 1

        print(f"  Looking up: {series_name} Volume {volume}")

        book_data = api.get_book_info(series_name, volume, project_state)

        if book_data:
            book = process_book_data(book_data, volume)
            print(f"  ✓ Success! Found: {book.book_title}")
            print(f"    Authors: {DataValidator.format_authors_list(book.authors)}")
            print(f"    Publisher: {book.publisher_name}")
            print(f"    MSRP: ${book.msrp_cost:.2f}" if book.msrp_cost else "    MSRP: Unknown")
            return True
        print("  ✗ No data found")
        return False

    except Exception as e:
        print(f"  ✗ Lookup Error: {e}")
        return False


def test_marc_export():
    """Test MARC export functionality"""
    print("📖 Testing MARC Export...")

    try:
        # Create test book data
        test_book = BookInfo(
            series_name="Test Series",
            volume_number=1,
            book_title="Test Series (Volume 1)",
            authors=["Test, Author"],
            msrp_cost=12.99,
            isbn_13="9781234567890",
            publisher_name="Test Publisher",
            copyright_year=2023,
            description="Test description",
            physical_description="200 pages",
            genres=["Test", "Genre"],
            warnings=[],
            barcode="T000001",
        )

        # Test export
        filename = "test_export.mrc"
        export_books_to_marc([test_book], filename, "T")

        # Check if file was created
        if os.path.exists(filename):
            print(f"  ✓ MARC export successful: {filename}")
            # Clean up
            os.remove(filename)
            return True
        print("  ✗ MARC file not created")
        return False

    except Exception as e:
        print(f"  ✗ MARC Export Error: {e}")
        return False


def main():
    """Run all tests"""
    print("🧪 Manga Lookup Tool - Core Logic Tests")
    print("=" * 50)
    print()

    # Run tests
    test_volume_parsing()
    test_barcode_generation()

    api_ok = test_api_connection()

    if api_ok:
        test_single_lookup()

    test_marc_export()

    print("=" * 50)
    print("✅ Core logic testing complete!")
    print()
    print("Next steps:")
    print("1. Push to GitHub")
    print("2. Deploy to Streamlit Cloud")
    print("3. Add DEEPSEEK_API_KEY to Streamlit secrets")


if __name__ == "__main__":
    main()
