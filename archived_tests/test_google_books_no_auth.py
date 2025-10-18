#!/usr/bin/env python3
"""
Test Google Books API without authentication
"""


import requests


def test_google_books_no_auth():
    """Test Google Books API without authentication"""
    print("🔍 Testing Google Books API without authentication...")

    # Test with a known ISBN
    test_isbn = "9781421580366"  # Tokyo Ghoul Vol 1
    url = "https://www.googleapis.com/books/v1/volumes"
    params = {
        "q": f"isbn:{test_isbn}",
        "maxResults": 1,
    }

    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()

        data = response.json()
        total_items = data.get("totalItems", 0)
        print(f"✅ Success! Found {total_items} items for ISBN {test_isbn}")

        if total_items > 0:
            item = data["items"][0]
            volume_info = item.get("volumeInfo", {})
            print(f"   Title: {volume_info.get('title', 'N/A')}")

            # Check for cover images
            image_links = volume_info.get("imageLinks", {})
            if image_links:
                print(f"   Cover images available: {list(image_links.keys())}")
                for size, url in image_links.items():
                    print(f"     {size}: {url}")
            else:
                print("   No cover images found")

        return True

    except Exception as e:
        print(f"❌ API request failed: {e}")
        return False

def main():
    print("🧪 Google Books API No-Auth Test")
    print("=" * 50)

    success = test_google_books_no_auth()

    if success:
        print("\n🎉 Google Books API works without authentication!")
        print("\n📝 You can now:")
        print("1. Run: python cache_cover_images.py")
        print("2. The script will use no authentication")
    else:
        print("\n❌ Google Books API requires authentication")
        print("\n📝 Alternative approach:")
        print("1. Get a simple Google Books API key")
        print("2. Set GOOGLE_BOOKS_API_KEY environment variable")
        print("3. Run: python cache_cover_images.py")

if __name__ == "__main__":
    main()
