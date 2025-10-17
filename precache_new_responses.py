#!/usr/bin/env python3
"""
Script to precache new DeepSeek API responses for all series and volumes in the database.

This script loads the existing project state, identifies all series and volumes from cached data,
and re-fetches the book information with the updated prompts to populate the cache with new responses.
"""

import os
import re
from manga_lookup import ProjectState, DeepSeekAPI

def extract_series_and_volume_from_prompt(prompt: str) -> tuple[str, int] | None:
    """Extract series_name and volume_number from the comprehensive prompt"""
    # Look for the series name and volume in the prompt
    match = re.search(r'Perform grounded deep research for the manga series "([^"]+)" volume (\d+)', prompt)
    if match:
        series_name = match.group(1)
        volume_number = int(match.group(2))
        return series_name, volume_number
    return None

def main():
    # Load project state
    ps = ProjectState()

    # Get all cached API calls
    # Assuming ProjectState has a way to get all cached prompts
    # For this implementation, we'll simulate by getting cache keys

    # Since the db is sqlite, we can query it directly
    import sqlite3

    conn = sqlite3.connect('project_state.db')
    cursor = conn.cursor()

    # Get all cached responses
    cursor.execute("SELECT prompt, volume FROM api_cache")
    cached_calls = cursor.fetchall()

    api = DeepSeekAPI()

    for prompt, volume in cached_calls:
        extracted = extract_series_and_volume_from_prompt(prompt)
        if extracted:
            series_name, volume_number = extracted
            print(f"Precaching {series_name} volume {volume_number}")
            # Call get_book_info to recache with new prompt
            try:
                api.get_book_info(series_name, volume_number, ps)
            except Exception as e:
                print(f"Error precaching {series_name} vol {volume_number}: {e}")

    conn.close()
    print("Precaching completed.")

if __name__ == "__main__":
    main()