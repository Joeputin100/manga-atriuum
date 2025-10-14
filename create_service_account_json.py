#!/usr/bin/env python3
"""
Create a service account JSON file from vertex.toml

This converts the TOML format service account credentials to JSON format
that can be used with Google authentication libraries.
"""

import os
import json

def create_service_account_json():
    """Convert vertex.toml to service-account.json"""
    vertex_path = "../vertex.toml"
    output_path = "google-credentials.json"

    if not os.path.exists(vertex_path):
        print(f"❌ Vertex credentials file not found: {vertex_path}")
        return False

    try:
        # Parse the TOML file
        import toml
        vertex_config = toml.load(vertex_path)
        vertex_ai = vertex_config.get('vertex_ai', {})

        # Create JSON structure
        service_account_info = {
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

        # Save as JSON
        with open(output_path, 'w') as f:
            json.dump(service_account_info, f, indent=2)

        print(f"✅ Created {output_path}")
        print(f"   Project: {service_account_info['project_id']}")
        print(f"   Service Account: {service_account_info['client_email']}")

        # Set environment variable for Google authentication
        os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = output_path
        print(f"✅ Set GOOGLE_APPLICATION_CREDENTIALS={output_path}")

        return True

    except Exception as e:
        print(f"❌ Error creating service account JSON: {e}")
        return False

def test_service_account_auth():
    """Test if service account authentication works"""
    print("\n🔍 Testing service account authentication...")

    try:
        from google.auth import default
        from google.auth.transport.requests import Request

        # Get default credentials (should use our service account)
        credentials, project = default()

        # Refresh token
        credentials.refresh(Request())

        print(f"✅ Service account authentication successful!")
        print(f"   Project: {project}")
        print(f"   Email: {credentials.service_account_email}")
        print(f"   Token: {credentials.token[:50]}...")

        return True

    except Exception as e:
        print(f"❌ Service account authentication failed: {e}")
        return False

def main():
    print("🔧 Service Account Setup for Google Books")
    print("=" * 50)

    # Create service account JSON file
    if create_service_account_json():
        # Test authentication
        if test_service_account_auth():
            print("\n🎉 Service account setup complete!")
            print("\n📝 Next steps:")
            print("1. The service account is now ready for use")
            print("2. For Google Books API, we still need to check if it works")
            print("3. Run: python try_google_books_with_service_account.py")
        else:
            print("\n❌ Service account authentication failed")
    else:
        print("\n❌ Failed to create service account JSON")

if __name__ == "__main__":
    main()