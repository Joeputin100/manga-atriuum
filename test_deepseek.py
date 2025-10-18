#!/usr/bin/env python3

import os
from manga_lookup import DeepSeekAPI, ProjectState

def test_deepseek_api():
    """Test DeepSeek API with Attack on Titan series"""

    # Load environment variables
    from dotenv import load_dotenv
    load_dotenv()

    # Check if API key is set
    api_key = os.getenv("DEEPSEEK_API_KEY")
    if not api_key:
        print("ERROR: DEEPSEEK_API_KEY not found in environment")
        return

    print(f"API Key found: {api_key[:10]}...")

    # Create API instance
    deepseek_api = DeepSeekAPI()
    print(f"DeepSeek API initialized with key: {deepseek_api.api_key[:10]}...")

    # Create project state
    project_state = ProjectState()

    # Test the API call for different series
    series_names = ["Attack on Titan", "Attack on Titan (Omnibus Edition)", "Attack on Titan (Colossal Edition)"]
    volume_number = 1

    for series_name in series_names:
        print(f"\nTesting API call for '{series_name}' volume {volume_number}...")

        try:
            book_data = deepseek_api.get_book_info(series_name, volume_number, project_state)
            if book_data:
                print("SUCCESS: API call returned data")
                print(f"Keys: {list(book_data.keys())}")
                print(f"Series name: {book_data.get('series_name')}")
                print(f"Book title: {book_data.get('book_title')}")
                print(f"Authors: {book_data.get('authors')}")
                print(f"Description: {book_data.get('description', 'No description')[:100]}...")
            else:
                print("ERROR: API call returned None")
        except Exception as e:
            print(f"EXCEPTION: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    test_deepseek_api()