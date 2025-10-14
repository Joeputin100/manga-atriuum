#!/usr/bin/env python3
"""
Try to use Vertex AI service account credentials for Google Books API

Note: This is experimental - Google Books API typically uses simple API keys
rather than service account OAuth2 authentication.
"""

import os
import json
import requests
from google.oauth2 import service_account
from google.auth.transport.requests import Request

def test_vertex_credentials_for_books():
    """Try to use Vertex credentials for Google Books API"""
    print("🔍 Testing Vertex credentials for Google Books API...")

    # Check if we can import the required libraries
    try:
        from google.oauth2 import service_account
        from google.auth.transport.requests import Request
    except ImportError:
        print("❌ Required libraries not installed")
        print("Install with: pip install google-auth requests")
        return False

    # Path to vertex.toml (adjust as needed)
    vertex_path = "../vertex.toml"

    if not os.path.exists(vertex_path):
        print(f"❌ Vertex credentials file not found: {vertex_path}")
        return False

    try:
        # Parse the TOML file
        import toml
        vertex_config = toml.load(vertex_path)
        vertex_ai = vertex_config.get('vertex_ai', {})

        # Create service account credentials
        credentials_info = {
            "type": vertex_ai.get("type"),
            "project_id": vertex_ai.get("project_id"),
            "private_key_id": vertex_ai.get("private_key_id"),
            "private_key": vertex_ai.get("private_key"),
            "client_email": vertex_ai.get("client_email"),
            "client_id": vertex_ai.get("client_id"),
            "auth_uri": vertex_ai.get("auth_uri"),
            "token_uri": vertex_ai.get("token_uri"),
            "auth_provider_x509_cert_url": vertex_ai.get("auth_provider_x509_cert_url"),
            "client_x509_cert_url": vertex_ai.get("client_x509_cert_url")
        }

        # Create credentials object
        credentials = service_account.Credentials.from_service_account_info(
            credentials_info,
            scopes=['https://www.googleapis.com/auth/books']
        )

        # Refresh the token
        credentials.refresh(Request())

        print(f"✅ Successfully authenticated with service account")
        print(f"   Project: {credentials.project_id}")
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

        response = requests.get(url, headers=headers, params=params, timeout=10)

        if response.status_code == 200:
            data = response.json()
            if data.get('totalItems', 0) > 0:
                print(f"✅ Service account works with Google Books API!")
                print(f"   Found {data['totalItems']} items for ISBN {test_isbn}")
                return True
            else:
                print(f"❌ No items found for ISBN {test_isbn}")
                return False
        else:
            print(f"❌ API request failed with status {response.status_code}")
            print(f"   Response: {response.text}")
            return False

    except Exception as e:
        print(f"❌ Error using Vertex credentials: {e}")
        return False

def main():
    print("🧪 Vertex Credentials Test for Google Books")
    print("=" * 50)

    # Try using Vertex credentials
    success = test_vertex_credentials_for_books()

    if success:
        print("\n🎉 Vertex credentials work with Google Books API!")
        print("\n📝 Note: This uses OAuth2 authentication which is more complex")
        print("   For simplicity, consider using a simple API key instead")
    else:
        print("\n❌ Vertex credentials don't work directly with Google Books API")
        print("\n📝 Recommendation:")
        print("1. Get a simple Google Books API key from Google Cloud Console")
        print("2. Set GOOGLE_BOOKS_API_KEY environment variable")
        print("3. Run: python cache_cover_images.py")

if __name__ == "__main__":
    main()