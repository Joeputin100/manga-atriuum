#!/usr/bin/env python3
"""
Setup script for Google Books API integration

This script helps set up the Google Books API key and provides
instructions for getting the API key from Google Cloud Console.
"""

import os
import sys

def check_api_key():
    """Check if Google Books API key is available"""
    api_key = os.getenv("GOOGLE_BOOKS_API_KEY")
    if api_key:
        print(f"✅ GOOGLE_BOOKS_API_KEY found")
        return True
    else:
        print("❌ GOOGLE_BOOKS_API_KEY not found")
        return False

def setup_instructions():
    """Print setup instructions for Google Books API"""
    print("\n📋 Google Books API Setup Instructions")
    print("=" * 50)
    print("""
Step 1: Get Google Books API Key

1. Go to Google Cloud Console: https://console.cloud.google.com/
2. Create a new project or select existing one
3. Enable the "Books API":
   - Go to "APIs & Services" > "Library"
   - Search for "Books API"
   - Click "Enable"

4. Create credentials:
   - Go to "APIs & Services" > "Credentials"
   - Click "Create Credentials" > "API key"
   - Copy the generated API key

Step 2: Set Environment Variable

For local development:
```bash
export GOOGLE_BOOKS_API_KEY='your-api-key-here'
```

For Streamlit Cloud:
1. Create a file `.streamlit/secrets.toml`
2. Add:
```toml
GOOGLE_BOOKS_API_KEY = "your-api-key-here"
```

Step 3: Test the Setup

Run: python test_google_books_api.py

Step 4: Cache Cover Images

Run: python cache_cover_images.py

This will fetch cover images for all 277 books with ISBN-13 data.
""")

def create_secrets_template():
    """Create a secrets.toml template for Streamlit Cloud"""
    template_content = """# Streamlit Secrets Configuration
# Copy this file to .streamlit/secrets.toml

# Google Books API Key
GOOGLE_BOOKS_API_KEY = "your-google-books-api-key-here"

# DeepSeek API Key (if not in environment)
DEEPSEEK_API_KEY = "your-deepseek-api-key-here"
"""

    secrets_path = ".streamlit/secrets.toml"

    # Create .streamlit directory if it doesn't exist
    os.makedirs(".streamlit", exist_ok=True)

    # Check if secrets file already exists
    if os.path.exists(secrets_path):
        print(f"⚠️  {secrets_path} already exists")
        with open(secrets_path, 'r') as f:
            existing_content = f.read()
        print(f"Current content:\n{existing_content}")
    else:
        # Create template
        with open(secrets_path, 'w') as f:
            f.write(template_content)
        print(f"✅ Created {secrets_path} template")
        print("Please edit this file with your actual API keys")

def main():
    print("🔧 Google Books API Setup")
    print("=" * 50)

    # Check current setup
    has_api_key = check_api_key()

    if has_api_key:
        print("\n🎉 API key is set up!")
        print("\nYou can now:")
        print("1. Test the API: python test_google_books_api.py")
        print("2. Cache cover images: python cache_cover_images.py")
        print("3. Deploy to Streamlit Cloud")
    else:
        # Provide setup instructions
        setup_instructions()

        # Create secrets template
        create_secrets_template()

        print("\n📝 Next Steps:")
        print("1. Follow the setup instructions above")
        print("2. Set the GOOGLE_BOOKS_API_KEY environment variable")
        print("3. Run this script again to verify setup")

if __name__ == "__main__":
    main()