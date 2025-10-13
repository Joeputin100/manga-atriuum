#!/usr/bin/env python3
"""
Test script to reproduce the trailing comma issue in author name formatting
"""

import sys
import os

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(__file__))

from manga_lookup import DataValidator

def test_author_formatting_trailing_comma():
    """Test author name formatting for trailing comma issue"""
    print("Testing author formatting for trailing comma issue...")

    # Test cases that might cause trailing comma issues
    test_cases = [
        (["Eiichiro Oda"], "Oda, Eiichiro"),
        (["Oda"], "Oda"),
        (["Eiichiro Oda", "Masashi Kishimoto"], "Oda, Eiichiro, Kishimoto, Masashi"),
        (["Oda,"], "Oda,"),  # Already has comma
        (["Oda, Eiichiro"], "Oda, Eiichiro"),  # Already formatted
        ([], ""),  # Empty list
    ]

    all_passed = True
    for input_authors, expected_output in test_cases:
        result = DataValidator.format_authors_list(input_authors)
        status = "✓ PASS" if result == expected_output else "✗ FAIL"
        print(f"  {status}: {input_authors} -> '{result}'")
        if result != expected_output:
            print(f"    Expected: '{expected_output}'")
            all_passed = False

    return all_passed

def test_single_author_edge_cases():
    """Test edge cases with single authors that might have trailing commas"""
    print("\nTesting single author edge cases...")

    test_cases = [
        (["Eiichiro Oda"], "Oda, Eiichiro"),
        (["Oda Eiichiro"], "Eiichiro, Oda"),  # This might be problematic
        (["Eiichiro"], "Eiichiro"),
        (["Oda"], "Oda"),
    ]

    all_passed = True
    for input_authors, expected_output in test_cases:
        result = DataValidator.format_authors_list(input_authors)
        status = "✓ PASS" if result == expected_output else "✗ FAIL"
        print(f"  {status}: {input_authors} -> '{result}'")
        if result != expected_output:
            print(f"    Expected: '{expected_output}'")
            all_passed = False

    return all_passed

if __name__ == "__main__":
    print("Running trailing comma tests...\n")

    test1_passed = test_author_formatting_trailing_comma()
    test2_passed = test_single_author_edge_cases()

    if test1_passed and test2_passed:
        print("\n✓ All trailing comma tests passed!")
    else:
        print("\n✗ Some trailing comma tests failed!")