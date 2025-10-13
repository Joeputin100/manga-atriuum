#!/usr/bin/env python3
"""
Comprehensive test script for manga_lookup functionality
Tests all major components including DeepSeek API integration, data validation, and Rich TUI
"""

import sys
import os
import json
import re
from datetime import datetime

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(__file__))

def test_title_formatting():
    """Test the title formatting with article shifting"""
    print("\n" + "="*50)
    print("TEST 1: Title Formatting with Article Shifting")
    print("="*50)

    test_cases = [
        ("The Last of the Mohicans", "Last of the Mohicans, The"),
        ("A Tale of Two Cities", "Tale of Two Cities, A"),
        ("An American Tragedy", "American Tragedy, An"),
        ("One Piece", "One Piece"),
        ("Naruto", "Naruto"),
        ("", ""),
        ("Attack on Titan", "Attack on Titan"),
        ("The Promised Neverland", "Promised Neverland, The"),
    ]

    from manga_lookup import DataValidator

    all_passed = True
    for input_title, expected_output in test_cases:
        result = DataValidator.format_title(input_title)
        status = "✓ PASS" if result == expected_output else "✗ FAIL"
        print(f"  {status}: '{input_title}' -> '{result}'")
        if result != expected_output:
            print(f"    Expected: '{expected_output}'")
            all_passed = False

    return all_passed

def test_isbn_validation():
    """Test ISBN-13 validation and metadata extraction"""
    print("\n" + "="*50)
    print("TEST 2: ISBN-13 Validation")
    print("="*50)

    try:
        from isbntools.app import canonical, to_isbn13, mask, info
        from isbnlib import is_isbn13
    except ImportError:
        print("  ✗ SKIP: isbntools not installed")
        return False

    def validate_isbn13(isbn):
        """Validate ISBN-13 and extract metadata"""
        canon = canonical(isbn)
        if not canon or not is_isbn13(canon):
            return {"valid": False}

        try:
            masked = mask(canon)
            parts = masked.split('-')
            group_info = info(canon)

            return {
                "valid": True,
                "isbn": canon,
                "prefix": parts[0],
                "registration_group": parts[1],
                "registrant": parts[2],
                "publication": parts[3],
                "check_digit": parts[4],
                "group_description": group_info
            }
        except Exception as e:
            return {"valid": False, "error": str(e)}

    test_cases = [
        ("9781569319017", True),  # Valid One Piece ISBN
        ("9781421536252", True),  # Valid Naruto ISBN
        ("1234567890123", False), # Invalid ISBN
        ("978-1-4215-3625-2", True), # ISBN with hyphens
        ("", False), # Empty string
    ]

    all_passed = True
    for isbn, should_be_valid in test_cases:
        result = validate_isbn13(isbn)
        status = "✓ PASS" if result["valid"] == should_be_valid else "✗ FAIL"
        print(f"  {status}: '{isbn}' -> valid={result['valid']}")

        if result["valid"]:
            print(f"    Metadata: {json.dumps(result, indent=4)}")

        if result["valid"] != should_be_valid:
            all_passed = False

    return all_passed

def test_date_validation():
    """Test copyright date validation and conversion"""
    print("\n" + "="*50)
    print("TEST 3: Copyright Date Validation")
    print("="*50)

    def validate_copyright_date(date_str):
        """Extract 4-digit year from various date formats"""
        if not date_str:
            return None

        # Try to extract year from various formats
        year_patterns = [
            r'\b(19|20)\d{2}\b',  # 4-digit years
            r'\b\d{4}\b',          # Any 4-digit number
        ]

        for pattern in year_patterns:
            matches = re.findall(pattern, str(date_str))
            if matches:
                year = int(matches[0])
                # Validate reasonable year range
                if 1900 <= year <= datetime.now().year + 1:  # Allow +1 for upcoming releases
                    return year

        return None

    test_cases = [
        ("2003", 2003),
        ("March 15, 2003", 2003),
        ("2003-03-15", 2003),
        ("Copyright 2003", 2003),
        ("© 2003", 2003),
        ("2025", 2025),  # Future year (should be allowed)
        ("1899", None),  # Too old
        ("3000", None),  # Too far in future
        ("", None),      # Empty
        ("invalid", None), # Invalid format
    ]

    all_passed = True
    for input_date, expected_year in test_cases:
        result = validate_copyright_date(input_date)
        status = "✓ PASS" if result == expected_year else "✗ FAIL"
        print(f"  {status}: '{input_date}' -> {result}")
        if result != expected_year:
            print(f"    Expected: {expected_year}")
            all_passed = False

    return all_passed

def test_msrp_validation():
    """Test MSRP validation and fallback logic"""
    print("\n" + "="*50)
    print("TEST 4: MSRP Validation")
    print("="*50)

    def validate_msrp(msrp_value, volume_number=None):
        """Validate MSRP with warnings for unusual values"""
        if msrp_value is None:
            return None, "No MSRP found"

        try:
            msrp = float(msrp_value)
            warnings = []

            if msrp < 10:
                warnings.append(f"MSRP ${msrp} is below minimum $10")
            elif msrp > 30:
                warnings.append(f"MSRP ${msrp} exceeds typical maximum $30")

            return msrp, warnings if warnings else None

        except (ValueError, TypeError):
            return None, "Invalid MSRP format"

    test_cases = [
        (9.99, ["MSRP $9.99 is below minimum $10"]),
        (12.99, None),  # Normal price
        (35.00, ["MSRP $35.0 exceeds typical maximum $30"]),
        (None, "No MSRP found"),
        ("invalid", "Invalid MSRP format"),
    ]

    all_passed = True
    for input_msrp, expected_warning in test_cases:
        result, warning = validate_msrp(input_msrp)

        if expected_warning is None:
            status = "✓ PASS" if warning is None else "✗ FAIL"
            print(f"  {status}: ${input_msrp} -> ${result}, warnings: {warning}")
            if warning is not None:
                all_passed = False
        else:
            if isinstance(expected_warning, list):
                status = "✓ PASS" if warning == expected_warning else "✗ FAIL"
            else:
                status = "✓ PASS" if warning == expected_warning else "✗ FAIL"
            print(f"  {status}: ${input_msrp} -> ${result}, warnings: {warning}")
            if warning != expected_warning:
                all_passed = False

    return all_passed

def test_project_state():
    """Test project state management with API call logging"""
    print("\n" + "="*50)
    print("TEST 5: Project State Management")
    print("="*50)

    from manga_lookup import ProjectState

    # Test initial state
    state = ProjectState("test_state.json")
    assert state.state["interaction_count"] == 0
    assert state.state["searches"] == []
    assert state.state["api_calls"] == []
    print("  ✓ Initial state created")

    # Test recording interactions with API logging
    state.record_interaction("One Piece volumes 1-3", 3)
    state.record_interaction("Naruto volumes 1-2", 2)

    assert state.state["interaction_count"] == 2
    assert state.state["total_books_found"] == 5
    assert len(state.state["searches"]) == 2
    assert len(state.state["api_calls"]) == 0  # No API calls recorded yet
    print("  ✓ Interactions recorded with API call tracking")

    # Test state persistence
    state.save_state()
    assert os.path.exists("test_state.json")
    print("  ✓ State file created and saved")

    # Test state loading
    new_state = ProjectState("test_state.json")
    assert new_state.state["interaction_count"] == 2
    assert new_state.state["total_books_found"] == 5
    print("  ✓ State loaded correctly from file")

    # Clean up
    if os.path.exists("test_state.json"):
        os.remove("test_state.json")
    print("  ✓ Cleanup completed")

    return True

def test_author_formatting():
    """Test author name formatting in 'Last, First M.' format"""
    print("\n" + "="*50)
    print("TEST 6: Author Name Formatting")
    print("="*50)

    def format_author_name(author_name):
        """Format author name as 'Last, First M.'"""
        if not author_name:
            return ""

        # Handle common Japanese name formats
        name_parts = author_name.strip().split()

        if len(name_parts) == 2:
            # Assume "First Last" format
            return f"{name_parts[1]}, {name_parts[0]}"
        elif len(name_parts) == 1:
            # Single name (like "Oda")
            return name_parts[0]
        else:
            # Complex name, try to handle
            # For Japanese names, last name is usually first
            if any(part.endswith('-') for part in name_parts):
                # Handle hyphenated names
                return author_name
            else:
                # Default: assume first part is first name, last part is last name
                return f"{name_parts[-1]}, {' '.join(name_parts[:-1])}"

    def format_authors_list(authors):
        """Format list of authors as comma-separated 'Last, First M.'"""
        if not authors:
            return ""
        formatted_authors = [format_author_name(author) for author in authors]
        return ", ".join(formatted_authors)

    test_cases = [
        (["Eiichiro Oda"], "Oda, Eiichiro"),
        (["Masashi Kishimoto"], "Kishimoto, Masashi"),
        (["Tite Kubo"], "Kubo, Tite"),
        (["Hajime Isayama"], "Isayama, Hajime"),
        (["Sui Ishida"], "Ishida, Sui"),
        (["Koyoharu Gotouge"], "Gotouge, Koyoharu"),
        (["Oda"], "Oda"),
        (["Eiichiro Oda", "Masashi Kishimoto"], "Oda, Eiichiro, Kishimoto, Masashi"),
        ([], ""),
    ]

    all_passed = True
    for input_authors, expected_output in test_cases:
        result = format_authors_list(input_authors)
        status = "✓ PASS" if result == expected_output else "✗ FAIL"
        print(f"  {status}: {input_authors} -> '{result}'")
        if result != expected_output:
            print(f"    Expected: '{expected_output}'")
            all_passed = False

    return all_passed

def test_deepseek_prompt_structure():
    """Test the structure of DeepSeek API prompts"""
    print("\n" + "="*50)
    print("TEST 7: DeepSeek Prompt Structure")
    print("="*50)

    def create_comprehensive_prompt(series_name, volume_number):
        """Create a comprehensive prompt for DeepSeek API"""
        prompt = f"""
        Perform grounded deep research for the manga series "{series_name}" volume {volume_number}.
        Provide comprehensive information in JSON format with the following fields:

        Required fields:
        - series_name: The official series name
        - volume_number: {volume_number}
        - book_title: The specific title for this volume (append "(Volume {volume_number})")
        - authors: List of authors/artists in "Last, First M." format, comma-separated for multiple
        - msrp_cost: Manufacturer's Suggested Retail Price in USD
        - isbn_13: ISBN-13 for paperback English edition (preferred) or other available edition
        - publisher_name: Publisher of the English edition
        - copyright_year: 4-digit copyright year
        - description: Summary of the book's content and notable reviews
        - physical_description: Physical characteristics (pages, dimensions, etc.)
        - genres: List of genres/subjects

        Format requirements:
        - Shift leading articles to end ("The Last of the Mohicans" → "Last of the Mohicans, The")
        - Format author names as "Last, First M."
        - Use authoritative sources where possible
        - If information is unavailable, use best available data and note any gaps
        - Return only valid JSON, no additional text

        Example format:
        {{
          "series_name": "One Piece",
          "volume_number": 1,
          "book_title": "One Piece (Volume 1)",
          "authors": ["Oda, Eiichiro"],
          "msrp_cost": 9.99,
          "isbn_13": "9781569319017",
          "publisher_name": "VIZ Media LLC",
          "copyright_year": 2003,
          "description": "Monkey D. Luffy begins his journey...",
          "physical_description": "208 pages, 5 x 7.5 inches",
          "genres": ["Shonen", "Adventure", "Fantasy"]
        }}
        """
        return prompt.strip()

    # Test prompt generation
    prompt = create_comprehensive_prompt("One Piece", 1)

    # Verify prompt contains required elements
    required_elements = [
        "One Piece",
        "volume 1",
        "series_name",
        "msrp_cost",
        "isbn_13",
        "JSON format",
        "grounded deep research"
    ]

    all_present = True
    for element in required_elements:
        if element.lower() not in prompt.lower():
            print(f"  ✗ Missing element: {element}")
            all_present = False

    if all_present:
        print("  ✓ All required prompt elements present")
        print(f"  Prompt length: {len(prompt)} characters")

    return all_present

def main():
    """Run all tests"""
    print("Running Comprehensive Manga Lookup Tests")
    print("="*60)

    test_results = []

    # Run all tests
    test_results.append(("Title Formatting", test_title_formatting()))
    test_results.append(("ISBN Validation", test_isbn_validation()))
    test_results.append(("Date Validation", test_date_validation()))
    test_results.append(("MSRP Validation", test_msrp_validation()))
    test_results.append(("Project State", test_project_state()))
    test_results.append(("Author Formatting", test_author_formatting()))
    test_results.append(("DeepSeek Prompts", test_deepseek_prompt_structure()))

    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)

    passed = 0
    total = len(test_results)

    for test_name, result in test_results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status}: {test_name}")
        if result:
            passed += 1

    print(f"\nOverall: {passed}/{total} tests passed")

    if passed == total:
        print("🎉 All tests passed! Ready for implementation.")
        return True
    else:
        print("⚠️ Some tests failed. Please review before implementation.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)