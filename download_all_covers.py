#!/usr/bin/env python3
"""
Download Cover Images for All Volumes and Series in Database

This script fetches and caches cover images for all manga volumes and series
stored in the project database using available APIs.
"""

import os
import time
import json
import sqlite3
from typing import List, Dict, Optional
from google_books_client import GoogleBooksClient
from mal_cover_fetcher import MALCoverFetcher
from mangadex_cover_fetcher import MangaDexCoverFetcher

class CoverDownloader:
    """Download and cache cover images for all manga data in database"""

    def __init__(self, db_file="project_state.db"):
        self.db_file = db_file
        self.google_client = GoogleBooksClient()
        self.mal_fetcher = MALCoverFetcher()
        self.mangadex_fetcher = MangaDexCoverFetcher()
        self._ensure_tables()

    def _ensure_tables(self):
        """Ensure required tables exist"""
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS cached_cover_images (
                id INTEGER PRIMARY KEY,
                isbn TEXT UNIQUE,
                url TEXT,
                timestamp TEXT
            )
        ''')

        conn.commit()
        conn.close()

    def get_all_series(self) -> List[str]:
        """Get all unique series names from project_state.json"""
        try:
            with open('project_state.json', 'r') as f:
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

    def get_all_volumes(self) -> List[Dict]:
        """Get all volumes with ISBN from project_state.json"""
        try:
            with open('project_state.json', 'r') as f:
                state = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return []

        volumes = []
        for api_call in state.get("api_calls", []):
            if api_call.get("success", False):
                try:
                    response = json.loads(api_call["response"])
                    isbn = response.get('isbn_13')
                    series = response.get('series_name')
                    volume_num = api_call.get("volume")
                    if isbn and series and volume_num:
                        volumes.append({
                            'series_name': series,
                            'volume_number': volume_num,
                            'isbn_13': isbn
                        })
                except json.JSONDecodeError:
                    continue
        return volumes

    def is_cover_cached(self, key: str) -> bool:
        """Check if cover is already cached"""
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()

        cursor.execute('SELECT url FROM cached_cover_images WHERE isbn = ?', (key,))
        result = cursor.fetchone()

        conn.close()
        return result is not None

    def cache_cover_url(self, key: str, url: str):
        """Cache cover URL in database"""
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()

        cursor.execute('''
            INSERT OR REPLACE INTO cached_cover_images (isbn, url, timestamp)
            VALUES (?, ?, datetime('now'))
        ''', (key, url))

        conn.commit()
        conn.close()

    def download_series_covers(self):
        """Download cover images for all series"""
        print("📚 Downloading series cover images...")
        series_list = self.get_all_series()
        print(f"Found {len(series_list)} unique series")

        success_count = 0
        for series_name in series_list:
            series_key = f"series:{series_name}"

            if self.is_cover_cached(series_key):
                print(f"✓ Already cached: {series_name}")
                continue

            print(f"Fetching cover for: {series_name}")
            cover_url = self.mal_fetcher.fetch_cover_for_series(series_name)

            if cover_url:
                self.cache_cover_url(series_key, cover_url)
                success_count += 1
            else:
                print(f"✗ Failed to get cover for: {series_name}")

            time.sleep(1)  # Rate limiting

        print(f"✓ Downloaded {success_count} series covers")

    def download_volume_covers(self):
        """Download cover images for all volumes"""
        print("📖 Downloading volume cover images...")
        volumes = self.get_all_volumes()
        print(f"Found {len(volumes)} volumes with ISBN")

        success_count = 0
        for volume in volumes:
            isbn = volume['isbn_13']
            series = volume['series_name']
            vol_num = volume['volume_number']

            if self.is_cover_cached(isbn):
                print(f"✓ Already cached: {series} Vol. {vol_num}")
                continue

            print(f"Fetching cover for: {series} Vol. {vol_num} (ISBN: {isbn})")
            cover_url = self.google_client.get_cover_image_url(isbn)
            if not cover_url:
                # Try MangaDex as fallback using series cover
                series_key = f"mangadex:{series}"
                if not self.is_cover_cached(series_key):
                    print(f"Trying MangaDex fallback for series: {series}")
                    cover_url = self.mangadex_fetcher.fetch_cover_for_series(series)
                    if cover_url:
                        self.cache_cover_url(series_key, cover_url)

            if cover_url:
                self.cache_cover_url(isbn, cover_url)
                success_count += 1
            else:
                print(f"✗ Failed to get cover for: {series} Vol. {vol_num}")

            time.sleep(0.2)  # Rate limiting

        print(f"✓ Downloaded {success_count} volume covers")

    def run(self):
        """Download all covers"""
        print("🚀 Starting cover image download for all manga data")
        print("=" * 60)

        self.download_series_covers()
        print()
        self.download_volume_covers()

        print("\n🎉 Cover download completed!")

def main():
    """Main entry point"""
    # Check API key for Google Books

    downloader = CoverDownloader()
    downloader.run()

if __name__ == "__main__":
    main()