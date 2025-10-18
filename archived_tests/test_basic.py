#!/usr/bin/env python3
"""
Basic test to verify the script works
"""

import os

from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_environment():
    """Test if environment variables are loaded"""
    api_key = os.getenv("DEEPSEEK_API_KEY")
    if api_key:
        print(f"✓ API Key loaded: {api_key[:10]}...")
        return True
    print("✗ API Key not found")
    return False

def test_imports():
    """Test if all required imports work"""
    try:
        import json

        import requests
        from rich.console import Console
        from rich.prompt import Prompt
        print("✓ All imports successful")
        return True
    except ImportError as e:
        print(f"✗ Import error: {e}")
        return False

if __name__ == "__main__":
    print("Testing basic functionality...")

    env_ok = test_environment()
    imports_ok = test_imports()

    if env_ok and imports_ok:
        print("\n✓ Basic setup is working!")
        print("You can now run: python manga_lookup_simple.py")
    else:
        print("\n✗ Setup has issues. Please check the errors above.")
