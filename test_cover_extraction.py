#!/usr/bin/env python3
"""
Test script to verify cover image extraction from project state
"""

import json
from cache_cover_images import extract_books_from_project_state

def test_cover_extraction():
    """Test that we can extract books with ISBN-13 from project state"""
    print("🔍 Testing cover image extraction from project state...")

    books = extract_books_from_project_state()

    if not books:
        print("❌ No books found in project state")
        return False

    print(f"✅ Found {len(books)} books with ISBN-13 data")

    # Show some sample books
    print("\n📚 Sample books found:")
    for i, book in enumerate(books[:5]):
        print(f"  {i+1}. {book['series_name']} Vol. {book['volume_number']} - ISBN: {book['isbn_13']}")

    if len(books) > 5:
        print(f"  ... and {len(books) - 5} more")

    return True

def test_cover_cache_loading():
    """Test that cover cache loading works"""
    print("\n📚 Testing cover cache loading...")

    from cache_cover_images import load_cover_cache

    cover_cache = load_cover_cache()

    if cover_cache:
        print(f"✅ Cover cache loaded with {len(cover_cache)} entries")
        print("Sample cache entries:")
        for i, (isbn, url) in enumerate(list(cover_cache.items())[:3]):
            print(f"  {i+1}. ISBN: {isbn}")
            print(f"     URL: {url[:80]}..." if len(url) > 80 else f"     URL: {url}")
    else:
        print("ℹ️  No cover cache found (this is normal before running cache_cover_images.py)")

    return True

if __name__ == "__main__":
    print("🧪 Cover Image Integration Test")
    print("=" * 50)

    success1 = test_cover_extraction()
    success2 = test_cover_cache_loading()

    if success1 and success2:
        print("\n🎉 All tests passed! The cover image integration is ready.")
        print("\n📝 Next steps:")
        print("1. Set GOOGLE_BOOKS_API_KEY environment variable")
        print("2. Run: python cache_cover_images.py")
        print("3. Deploy to Streamlit Cloud with the API key in secrets")
    else:
        print("\n❌ Some tests failed. Please check the implementation.")