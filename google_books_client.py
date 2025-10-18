#!/usr/bin/env python3
"""
Google Books API Client for fetching cover images

This module provides functionality to fetch cover image URLs from Google Books API
using ISBN-13 numbers. It includes caching and rate limiting.
"""

import os
import time

import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class GoogleBooksClient:
    """Client for Google Books API with rate limiting and caching"""

    def __init__(self):
        self.base_url = "https://www.googleapis.com/books/v1/volumes"
        self.last_request_time = 0
        self.min_request_interval = 0.1  # 100ms between requests (10 requests/second)

    def _rate_limit(self):
        """Implement basic rate limiting"""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time

        if time_since_last < self.min_request_interval:
            time.sleep(self.min_request_interval - time_since_last)

        self.last_request_time = time.time()

    def get_cover_image_url(self, isbn_13: str) -> str | None:
        """
        Fetch cover image URL from Google Books API using ISBN-13
        Downloads and caches the image locally, returns local URL

        Args:
            isbn_13: ISBN-13 number as string

        Returns:
            Local URL string for cached cover image or None if not found
        """
        if not isbn_13:
            return None

        self._rate_limit()

        # Construct the keyless API URL
        url = f"{self.base_url}?q=isbn:{isbn_13}&maxResults=1"

        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()

            data = response.json()

            # Check if we found any books
            if data.get("totalItems", 0) == 0:
                return None

            # Get the first item
            item = data["items"][0]
            volume_info = item.get("volumeInfo", {})

            # Try to get the largest available cover image
            image_links = volume_info.get("imageLinks", {})

            # Prefer larger images, fall back to smaller ones
            for image_size in ["extraLarge", "large", "medium", "small", "thumbnail", "smallThumbnail"]:
                if image_size in image_links:
                    cover_url = image_links[image_size]
                    try:
                        # Download and cache the image
                        img_response = requests.get(cover_url, timeout=10)
                        img_response.raise_for_status()

                        # Save to cache
                        os.makedirs("cache/images", exist_ok=True)
                        filename = f"{isbn_13.replace('-', '_')}.jpg"
                        filepath = f"cache/images/{filename}"
                        with open(filepath, "wb") as f:
                            f.write(img_response.content)

                        # Return local URL
                        return f"/images/{filename}"

                    except Exception as download_error:
                        print(f"Error downloading image for ISBN {isbn_13}: {download_error}")
                        continue

            return None

        except requests.exceptions.RequestException as e:
            print(f"Error fetching cover image for ISBN {isbn_13}: {e}")
            return None
        except (KeyError, IndexError) as e:
            print(f"Error parsing Google Books response for ISBN {isbn_13}: {e}")
            return None

def get_cover_image_url(isbn_13: str) -> str | None:
    """
    Convenience function to get cover image URL
    Downloads and caches the image, returns local URL

    Args:
        isbn_13: ISBN-13 number as string

    Returns:
        Local URL string for cached cover image or None if not found
    """
    client = GoogleBooksClient()
    return client.get_cover_image_url(isbn_13)

if __name__ == "__main__":
    # Test the client with a known ISBN
    test_isbn = "9781569319017"  # One Piece Volume 1
    cover_url = get_cover_image_url(test_isbn)
    print(f"Cover URL for {test_isbn}: {cover_url}")
