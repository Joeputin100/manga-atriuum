#!/usr/bin/env python3
"""
Test if service account can access Google Books API
"""

import os
import requests
from google.auth import default
from google.auth.transport.requests import Request

def test_service_account_books_api():
    """Test if service account can access Google Books API"""
    print("🔍 Testing service account with Google Books API...")

    try:
        # Get default credentials (should use our service account)
        credentials, project = default()

        # Refresh token
        credentials.refresh(Request())

        print(f"✅ Service account authenticated")
        print(f"   Project: {project}")
        print(f"   Email: {credentials.service_account_email}")

        # Try to use the token for Google Books API
        headers = {
            'Authorization': f'Bearer {credentials.token}',
            'Content-Type': 'application/json'
        }

        # Test with Google Books API
        test_isbn = "9781421580366"  # Tokyo Ghoul Vol 1
        url = "https://www.googleapis.com/books/v1/volumes"
        params = {
            'q': f'isbn:{test_isbn}'
        }

        print(f"📚 Making request for ISBN: {test_isbn}")
        response = requests.get(url, headers=headers, params=params, timeout=10)

        print(f"📊 Response status: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            total_items = data.get('totalItems', 0)
            print(f"✅ Success! Found {total_items} items")

            if total_items > 0:
                item = data['items'][0]
                volume_info = item.get('volumeInfo', {})
                print(f"   Title: {volume_info.get('title', 'N/A')}")

                # Check for cover images
                image_links = volume_info.get('imageLinks', {})
                if image_links:
                    print(f"   Cover images: {list(image_links.keys())}")
                    for size, url in image_links.items():
                        print(f"     {size}: {url}")
                else:
                    print("   No cover images found")

            return True
        else:
            print(f"❌ API request failed")
            print(f"   Response: {response.text}")
            return False

    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def main():
    print("🧪 Service Account Google Books Test")
    print("=" * 50)

    # Check if credentials are set
    creds_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
    if not creds_path:
        print("❌ GOOGLE_APPLICATION_CREDENTIALS not set")
        print("Run: export GOOGLE_APPLICATION_CREDENTIALS='google-credentials.json'")
        return

    if not os.path.exists(creds_path):
        print(f"❌ Credentials file not found: {creds_path}")
        return

    print(f"✅ Using credentials: {creds_path}")

    # Test the service account
    success = test_service_account_books_api()

    if success:
        print("\n🎉 Service account works with Google Books API!")
        print("\n📝 You can now:")
        print("1. Run: python cache_cover_images.py")
        print("2. The script will use service account authentication")
    else:
        print("\n❌ Service account doesn't work with Google Books API")
        print("\n📝 Alternative approach:")
        print("1. Get a simple Google Books API key")
        print("2. Set GOOGLE_BOOKS_API_KEY environment variable")
        print("3. Run: python cache_cover_images.py")

if __name__ == "__main__":
    main()