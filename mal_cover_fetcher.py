#!/usr/bin/env python3
"""
MyAnimeList Cover Image Fetcher

Uses Jikan API to fetch manga cover images from MyAnimeList.
Downloads and caches images locally.
"""

import os
import time
import requests
from typing import Optional
import sqlite3

class MALCoverFetcher:
    """Fetch manga covers from MyAnimeList using Jikan API"""
    
    def __init__(self):
        self.base_url = "https://api.jikan.moe/v4"
        self.last_request_time = 0
        self.min_request_interval = 2  # 2 seconds between requests (respectful rate limiting)
    
    def _rate_limit(self):
        """Rate limiting to be respectful to the API"""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        
        if time_since_last < self.min_request_interval:
            time.sleep(self.min_request_interval - time_since_last)
        
        self.last_request_time = time.time()
    
    def search_manga(self, title: str) -> Optional[dict]:
        """Search for manga by title"""
        self._rate_limit()
        
        params = {
            'q': title,
            'type': 'manga',
            'limit': 5  # Get top 5 results
        }
        
        try:
            response = requests.get(f"{self.base_url}/manga", params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            if data.get('data') and len(data['data']) > 0:
                # Return the first (most relevant) result
                return data['data'][0]
            
        except Exception as e:
            print(f"Error searching MAL for '{title}': {e}")
        
        return None
    
    def get_cover_url(self, manga_data: dict) -> Optional[str]:
        """Extract cover image URL from manga data"""
        try:
            images = manga_data.get('images', {})
            jpg_images = images.get('jpg', {})
            # Prefer large image, fallback to image_url
            return jpg_images.get('large_image_url') or jpg_images.get('image_url')
        except:
            return None
    
    def download_and_cache_image(self, image_url: str, series_name: str) -> Optional[str]:
        """Download image and cache locally"""
        if not image_url:
            return None
        
        try:
            # Create cache directory
            os.makedirs('cache/images', exist_ok=True)
            
            # Generate filename from series name
            safe_name = "".join(c for c in series_name if c.isalnum() or c in (' ', '-', '_')).rstrip()
            safe_name = safe_name.replace(' ', '_')
            filename = f"{safe_name}.jpg"
            filepath = f"cache/images/{filename}"
            
            # Download image
            img_response = requests.get(image_url, timeout=15)
            img_response.raise_for_status()
            
            # Save to cache
            with open(filepath, 'wb') as f:
                f.write(img_response.content)
            
            print(f"✓ Downloaded cover for '{series_name}'")
            return f"/images/{filename}"
            
        except Exception as e:
            print(f"✗ Error downloading image for '{series_name}': {e}")
            return None
    
    def fetch_cover_for_series(self, series_name: str) -> Optional[str]:
        """Fetch and cache cover image for a manga series"""
        print(f"Searching MAL for '{series_name}'...")
        
        manga_data = self.search_manga(series_name)
        if not manga_data:
            print(f"✗ No results found for '{series_name}'")
            return None
        
        cover_url = self.get_cover_url(manga_data)
        if not cover_url:
            print(f"✗ No cover image found for '{series_name}'")
            return None
        
        print(f"Found cover: {cover_url}")
        
        return self.download_and_cache_image(cover_url, series_name)

def get_all_series_from_db() -> list:
    """Get all unique series names from the database"""
    db = sqlite3.connect('project_state.db')
    cursor = db.cursor()
    
    try:
        cursor.execute('SELECT DISTINCT series_name FROM cover_comparison_results')
        series = [row[0] for row in cursor.fetchall()]
    except sqlite3.OperationalError:
        # Fallback to old searches table
        cursor.execute('SELECT DISTINCT query FROM searches')
        series = [row[0] for row in cursor.fetchall()]
    
    db.close()
    return series

def update_series_cover_in_db(series_name: str, cover_url: str):
    """Update the database with cover URL for a series"""
    db = sqlite3.connect('project_state.db')
    cursor = db.cursor()
    
    try:
        # Update cover_comparison_results if exists
        cursor.execute('''
            UPDATE cover_comparison_results 
            SET google_cover = ? 
            WHERE series_name = ? AND google_cover IS NULL
        ''', (cover_url, series_name))
        
        # Also update any other relevant tables
        # For now, just log the cover
        print(f"Updated DB: {series_name} -> {cover_url}")
        
    except Exception as e:
        print(f"Error updating DB for {series_name}: {e}")
    
    db.commit()
    db.close()

def main():
    """Download covers for all series in database"""
    print("Starting MAL cover image download...")
    
    fetcher = MALCoverFetcher()
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
