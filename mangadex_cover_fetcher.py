#!/usr/bin/env python3
import json

"""
MangaDex Cover Image Fetcher

Uses MangaDex API to fetch manga cover images.
Downloads and caches images locally.
"""

import os
import sqlite3
import time

import requests


class MangaDexCoverFetcher:
    """Fetch manga covers from MangaDex API"""

    def __init__(self):
        self.base_url = "https://api.mangadex.org"
        self.last_request_time = 0
        self.min_request_interval = 0.5  # 500ms between requests (respectful rate limiting)

    def _rate_limit(self):
        """Rate limiting to be respectful to the API"""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time

        if time_since_last < self.min_request_interval:
            time.sleep(self.min_request_interval - time_since_last)

        self.last_request_time = time.time()

    def search_manga(self, title: str) -> dict | None:
        """Search for manga by title"""
        self._rate_limit()

        params = {
            "title": title,
            "limit": 5,  # Get top 5 results
            "includes[]": ["cover_art"],
        }

        try:
            response = requests.get(f"{self.base_url}/manga", params=params, timeout=10)
            response.raise_for_status()

            data = response.json()

            if data.get("data") and len(data["data"]) > 0:
                # Return the first (most relevant) result
                return data["data"][0]

        except Exception as e:
            print(f"Error searching MangaDex for '{title}': {e}")

        return None

    def get_cover_url(self, manga_data: dict) -> str | None:
        """Extract cover image URL from manga data"""
        try:
            relationships = manga_data.get("relationships", [])
            for rel in relationships:
                if rel.get("type") == "cover_art":
                    cover_id = rel["id"]
                    # Get the cover filename
                    self._rate_limit()
                    cover_response = requests.get(f"{self.base_url}/cover/{cover_id}", timeout=10)
                    cover_response.raise_for_status()
                    cover_data = cover_response.json()
                    filename = cover_data["data"]["attributes"]["fileName"]
                    return f"https://uploads.mangadex.org/covers/{manga_data['id']}/{filename}"
        except Exception as e:
            print(f"Error getting cover URL: {e}")
        return None

    def download_and_cache_image(self, image_url: str, series_name: str) -> str | None:
        """Download image and cache locally"""
        if not image_url:
            return None

        try:
            # Create cache directory
            os.makedirs("cache/images", exist_ok=True)

            # Generate filename from series name
            safe_name = "".join(c for c in series_name if c.isalnum() or c in (" ", "-", "_")).rstrip()
            safe_name = safe_name.replace(" ", "_")
            filename = f"{safe_name}_mangadex.jpg"
            filepath = f"cache/images/{filename}"

            # Download image
            img_response = requests.get(image_url, timeout=15)
            img_response.raise_for_status()

            # Save to cache
            with open(filepath, "wb") as f:
                f.write(img_response.content)

            print(f"✓ Using direct image URL for '{series_name}'")
            return f"/images/{filename}"

        except Exception as e:
            print(f"✗ Error downloading image for '{series_name}': {e}")
            return None

    def fetch_cover_for_series(self, series_name: str) -> str | None:
        """Fetch and cache cover image for a manga series"""
        print(f"Searching MangaDex for '{series_name}'...")

        manga_data = self.search_manga(series_name)
        if not manga_data:
            print(f"✗ No results found for '{series_name}'")
            return None

        cover_url = self.get_cover_url(manga_data)
        if not cover_url:
            print(f"✗ No cover image found for '{series_name}'")
            return None

        print(f"Found cover: {cover_url}")

        print(f"✓ Using direct image URL for '{series_name}'")
        return cover_url

def get_all_series_from_db() -> list:

    """Get all unique series names from project_state.json"""

    try:

        with open("project_state.json") as f:

            state = json.load(f)

    except (FileNotFoundError, json.JSONDecodeError):

        return []



    series = set()

    for api_call in state.get("api_calls", []):

        if api_call.get("success", False):

            try:

                response = json.loads(api_call["response"])

                series_name = response.get("series_name")

                if series_name:

                    series.add(series_name)

            except json.JSONDecodeError:

                continue

    return list(series)
    return series

def update_series_cover_in_db(series_name: str, cover_url: str):
    """Update the database with cover URL for a series"""
    db = sqlite3.connect("project_state.db")
    cursor = db.cursor()

    try:
        # Update cover_comparison_results if exists
        cursor.execute("""
            UPDATE cover_comparison_results
            SET google_cover = ?
            WHERE series_name = ?
        """, (cover_url, series_name))

        # Also update cached_cover_images
        cursor.execute("""
            INSERT OR REPLACE INTO cached_cover_images (isbn, url, timestamp)
            VALUES (?, ?, datetime('now'))
        """, (f"mangadex:{series_name}", cover_url))

        print(f"Updated DB: {series_name} -> {cover_url}")

    except Exception as e:
        print(f"Error updating DB for {series_name}: {e}")

    db.commit()
    db.close()

def main():
    """Download covers for all series in database"""
    print("Starting MangaDex cover image download...")

    fetcher = MangaDexCoverFetcher()
    series_list = get_all_series_from_db()

    print(f"Found {len(series_list)} series in database")

    success_count = 0

    for series_name in series_list:
        cover_url = fetcher.fetch_cover_for_series(series_name)

        if cover_url:
            update_series_cover_in_db(series_name, cover_url)
            success_count += 1

        # Small delay between series
        time.sleep(1)

    print(f"\nCompleted! Downloaded covers for {success_count}/{len(series_list)} series")

if __name__ == "__main__":
    main()
