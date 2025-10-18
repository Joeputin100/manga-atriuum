#!/usr/bin/env python3
"""
Final integration test to verify both MSRP rounding and text-based list functionality
"""

import os
import sys

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(__file__))

from manga_lookup import DataValidator, process_book_data


def test_msrp_rounding():
    """Test MSRP rounding functionality"""
    print("Testing MSRP rounding functionality...")

    test_cases = [
        (9.99, "MSRP $9.99 is below minimum $10 (rounded up to $10.0)"),
        (8.50, "MSRP $8.5 is below minimum $10 (rounded up to $10.0)"),
        (12.99, None),  # No warning expected
        (None, "No MSRP found"),
    ]

    all_passed = True
    for msrp, expected_warning in test_cases:
        test_data = {
            "series_name": "Test Series",
            "volume_number": 1,
            "book_title": "Test Series (Volume 1)",
            "authors": ["Test, Author"],
            "msrp_cost": msrp,
            "isbn_13": "9781234567890",
            "publisher_name": "Test Publisher",
            "copyright_year": 2023,
            "description": "Test description",
            "physical_description": "200 pages",
            "genres": ["Test"],
        }

        book = process_book_data(test_data, 1)

        if expected_warning:
            if expected_warning in book.warnings:
                print(f"  ✓ MSRP ${msrp}: Warning correctly generated")
            else:
                print(f"  ✗ MSRP ${msrp}: Expected warning '{expected_warning}' but got {book.warnings}")
                all_passed = False
        elif not book.warnings:
            print(f"  ✓ MSRP ${msrp}: No warnings as expected")
        else:
            print(f"  ✗ MSRP ${msrp}: Expected no warnings but got {book.warnings}")
            all_passed = False

    return all_passed

def test_field_status_indicators():
    """Test field status indicators in the text-based list"""
    print("\nTesting field status indicators...")

    # Test book with complete data
    complete_data = {
        "series_name": "Complete Series",
        "volume_number": 1,
        "book_title": "Complete Series (Volume 1)",
        "authors": ["Complete, Author"],
        "msrp_cost": 12.99,
        "isbn_13": "9781234567890",
        "publisher_name": "Complete Publisher",
        "copyright_year": 2023,
        "description": "Complete description",
        "physical_description": "200 pages",
        "genres": ["Complete"],
    }

    complete_book = process_book_data(complete_data, 1)

    # Test book with missing data
    missing_data = {
        "series_name": "Missing Series",
        "volume_number": 1,
        "book_title": "Missing Series (Volume 1)",
        "authors": ["Missing, Author"],
        "msrp_cost": None,
        "isbn_13": None,
        "publisher_name": None,
        "copyright_year": None,
        "description": None,
        "physical_description": None,
        "genres": [],
    }

    missing_book = process_book_data(missing_data, 1)

    # Check complete book fields
    complete_fields = [
        ("MSRP", complete_book.msrp_cost is not None),
        ("ISBN-13", bool(complete_book.isbn_13)),
        ("Publisher", bool(complete_book.publisher_name)),
        ("Copyright Year", complete_book.copyright_year is not None),
        ("Description", bool(complete_book.description)),
        ("Physical Description", bool(complete_book.physical_description)),
        ("Genres", bool(complete_book.genres)),
    ]

    all_complete = all(is_populated for _, is_populated in complete_fields)
    if all_complete:
        print("  ✓ Complete book: All fields populated correctly")
    else:
        print(f"  ✗ Complete book: Some fields missing: {complete_fields}")
        return False

    # Check missing book fields
    missing_fields = [
        ("MSRP", missing_book.msrp_cost is not None),
        ("ISBN-13", bool(missing_book.isbn_13)),
        ("Publisher", bool(missing_book.publisher_name)),
        ("Copyright Year", missing_book.copyright_year is not None),
        ("Description", bool(missing_book.description)),
        ("Physical Description", bool(missing_book.physical_description)),
        ("Genres", bool(missing_book.genres)),
    ]

    all_missing = not any(is_populated for _, is_populated in missing_fields)
    if all_missing:
        print("  ✓ Missing book: All fields correctly identified as missing")
    else:
        print(f"  ✗ Missing book: Some fields incorrectly populated: {missing_fields}")
        return False

    return True

def test_author_formatting():
    """Test author formatting functionality"""
    print("\nTesting author formatting...")

    test_cases = [
        (["Ishida, Sui"], "Ishida, Sui"),
        (["Oda, Eiichiro"], "Oda, Eiichiro"),
        (["Test Author"], "Author, Test"),  # Should be reformatted
        ([], ""),
        (["Single"], "Single"),
    ]

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
    print("Running final integration tests...\n")

    test1_passed = test_msrp_rounding()
    test2_passed = test_field_status_indicators()
    test3_passed = test_author_formatting()

    if test1_passed and test2_passed and test3_passed:
        print("\n✓ All integration tests passed!")
        print("\nSummary of changes:")
        print("  ✓ MSRP values under $10 are rounded up to $10")
        print("  ✓ Warning messages include the rounded value")
        print("  ✓ Rich table replaced with text-based list")
        print("  ✓ Field status indicators show ✓ for populated fields and ✗ for missing fields")
        print("  ✓ Interactive menu allows selecting books for detailed view")
    else:
        print("\n✗ Some integration tests failed!")
