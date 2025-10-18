#!/usr/bin/env python3
"""
Test Google Books API with different authentication methods
"""

import os

import requests


def test_with_api_key():
    """Test Google Books API with API key authentication"""
    api_key = os.getenv("GOOGLE_BOOKS_API_KEY")
    if not api_key:
        print("❌ GOOGLE_BOOKS_API_KEY not found in environment")
        return False

    print("🔍 Testing Google Books API with API key...")

    # Test with a known ISBN
    test_isbn = "9781421580366"  # Tokyo Ghoul Vol 1
    url = "https://www.googleapis.com/books/v1/volumes"
    params = {
        "q": f"isbn:{test_isbn}",
        "key": api_key,
    }

    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()

        data = response.json()
        if data.get("totalItems", 0) > 0:
            print(f"✅ API key works! Found {data['totalItems']} items for ISBN {test_isbn}")

            # Show sample data
            item = data["items"][0]
            volume_info = item.get("volumeInfo", {})
            print(f"   Title: {volume_info.get('title', 'N/A')}")

            # Check for cover images
            image_links = volume_info.get("imageLinks", {})
            if image_links:
                print(f"   Cover images available: {list(image_links.keys())}")
            else:
                print("   No cover images found")

            return True
        print(f"❌ No items found for ISBN {test_isbn}")
        return False

    except Exception as e:
        print(f"❌ API key test failed: {e}")
        return False

def test_with_service_account():
    """Test if we can use service account for Google Books API"""
    print("\n🔍 Testing service account credentials...")

    # For Google Books API, service accounts typically require OAuth2
    # which is more complex than simple API key
    print("⚠️  Service account authentication requires OAuth2 flow")
    print("   This is more complex than API key authentication")
    print("   Recommended: Use simple API key for Google Books API")

    return False

def main():
    print("🧪 Google Books API Authentication Test")
    print("=" * 50)

    # Check environment variables
    api_key = os.getenv("GOOGLE_BOOKS_API_KEY")

    if api_key:
        print("✅ GOOGLE_BOOKS_API_KEY found in environment")
        success = test_with_api_key()
    else:
        print("❌ GOOGLE_BOOKS_API_KEY not found")
        print("\n📝 To set up:")
        print("1. Get Google Books API key from: https://console.cloud.google.com/")
        print("2. Set environment variable: export GOOGLE_BOOKS_API_KEY='your-key'")
        print("3. For Streamlit Cloud: Add to secrets.toml")
        success = False

    if success:
        print("\n🎉 Ready to cache cover images!")
        print("Run: python cache_cover_images.py")
    else:
        print("\n❌ Need to set up Google Books API key first")

if __name__ == "__main__":
    main()
