#!/usr/bin/env python3
"""
Cover Image Caching Script

This script processes the existing project state and caches cover image URLs
for all books that have ISBN-13 data using the Google Books API.
"""

import json
import time

from google_books_client import GoogleBooksClient


def extract_books_from_project_state(project_state_file: str = "project_state.json") -> list[dict]:
    """
    Extract all books with ISBN-13 data from project state

    Returns:
        List of book dictionaries with series_name, volume_number, and isbn_13
    """
    try:
        with open(project_state_file) as f:
            state = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"Error loading project state: {e}")
        return []

    books = []

    # Extract books from cached API responses
    for api_call in state.get("api_calls", []):
        if api_call.get("success", False):
            try:
                # Parse the response to get book data
                response_data = json.loads(api_call["response"])

                # Check if we have ISBN-13 data
                isbn_13 = response_data.get("isbn_13")
                if isbn_13:
                    books.append({
                        "series_name": response_data.get("series_name"),
                        "volume_number": api_call.get("volume"),
                        "isbn_13": isbn_13,
                        "raw_data": response_data,
                    })
            except (json.JSONDecodeError, KeyError) as e:
                print(f"Error parsing API response: {e}")
                continue

    return books

def cache_cover_images_for_books(books: list[dict]) -> dict[str, str]:
    """
    Cache cover image URLs for all books with ISBN-13 data

    Args:
        books: List of book dictionaries with ISBN-13 data

    Returns:
        Dictionary mapping ISBN-13 to cover image URL
    """
    client = GoogleBooksClient()
    cover_cache = {}

    print(f"Processing {len(books)} books with ISBN-13 data...")

    for i, book in enumerate(books, 1):
        isbn_13 = book["isbn_13"]
        series_name = book["series_name"]
        volume_number = book["volume_number"]

        print(f"[{i}/{len(books)}] Fetching cover for {series_name} Vol. {volume_number} (ISBN: {isbn_13})...")

        # Skip if we already have this ISBN cached
        if isbn_13 in cover_cache:
            print("  ✓ Already cached")
            continue

        # Fetch cover image URL
        cover_url = client.get_cover_image_url(isbn_13)

        if cover_url:
            cover_cache[isbn_13] = cover_url
            print(f"  ✓ Found cover: {cover_url}")
        else:
            print("  ✗ No cover found")

        # Small delay to be respectful to the API
        time.sleep(0.2)

    return cover_cache

def save_cover_cache(cover_cache: dict[str, str], cache_file: str = "cover_cache.json"):
    """Save cover cache to JSON file"""
    try:
        with open(cache_file, "w") as f:
            json.dump(cover_cache, f, indent=2)
        print(f"✓ Cover cache saved to {cache_file} ({len(cover_cache)} covers)")
    except OSError as e:
        print(f"Error saving cover cache: {e}")

def load_cover_cache(cache_file: str = "cover_cache.json") -> dict[str, str]:
    """Load cover cache from JSON file"""
    try:
        with open(cache_file) as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}

def update_project_state_with_covers(cover_cache: dict[str, str], project_state_file: str = "project_state.json"):
    """
    Update project state with cover image URLs

    This function modifies the project state to include cover_image_url
    in the cached responses for future use.
    """
    try:
        with open(project_state_file) as f:
            state = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"Error loading project state for update: {e}")
        return

    updated_count = 0

    # Update cached API responses with cover URLs
    for api_call in state.get("api_calls", []):
        if api_call.get("success", False):
            try:
                response_data = json.loads(api_call["response"])
                isbn_13 = response_data.get("isbn_13")

                if isbn_13 and isbn_13 in cover_cache:
                    # Add cover URL to the response data
                    response_data["cover_image_url"] = cover_cache[isbn_13]

                    # Update the API call response
                    api_call["response"] = json.dumps(response_data)
                    updated_count += 1

            except (json.JSONDecodeError, KeyError):
                continue

    # Save updated state
    try:
        with open(project_state_file, "w") as f:
            json.dump(state, f, indent=2)
        print(f"✓ Updated project state with {updated_count} cover URLs")
    except OSError as e:
        print(f"Error saving updated project state: {e}")

def main():
    """Main function to cache cover images"""
    print("📚 Cover Image Caching Script")
    print("=" * 50)

    # Check if Google Books API key is available
    import os
    if not os.getenv("GOOGLE_BOOKS_API_KEY"):
        print("⚠️  GOOGLE_BOOKS_API_KEY not found in environment variables")
        print("   Please set the API key before running this script")
        return

    # Extract books from project state
    books = extract_books_from_project_state()

    if not books:
        print("No books with ISBN-13 data found in project state")
        return

    print(f"Found {len(books)} books with ISBN-13 data")

    # Cache cover images
    cover_cache = cache_cover_images_for_books(books)

    if cover_cache:
        # Save cover cache
        save_cover_cache(cover_cache)

        # Update project state with cover URLs
        update_project_state_with_covers(cover_cache)

        print(f"\n🎉 Successfully cached {len(cover_cache)} cover images")
    else:
        print("\n❌ No cover images were found")

if __name__ == "__main__":
    main()
