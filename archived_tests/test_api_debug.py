#!/usr/bin/env python3
"""
Quick test script to debug DeepSeek API for series name correction
"""

import sys

sys.path.append(".")

from manga_lookup import DeepSeekAPI


def test_api():
    """Test the DeepSeek API directly"""
    print("Testing DeepSeek API...")

    try:
        api = DeepSeekAPI()
        print("✅ API initialized successfully")
    except ValueError as e:
        print(f"❌ API initialization failed: {e}")
        return

    # Test with a sample series name
    test_series = "Blue Exorcist"
    print(f"\nTesting with series: '{test_series}'")

    try:
        suggestions = api.correct_series_name(test_series)
        print("✅ Suggestions returned:")
        print(f"   {suggestions}")
        print(f"   Number of suggestions: {len(suggestions)}")
    except Exception as e:
        print(f"❌ Error getting suggestions: {e}")

if __name__ == "__main__":
    test_api()
