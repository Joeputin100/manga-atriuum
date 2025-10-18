#!/usr/bin/env python3
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
"""
Real Cover Image Comparison Test

Compares actual cover image URLs from DeepSeek API vs Google Books API (keyless)
"""

import json
import os
import sqlite3
import time
from datetime import datetime

import requests
from dotenv import load_dotenv

# Load environment
load_dotenv()

# DeepSeek API setup
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
DEEPSEEK_URL = "https://api.deepseek.com/v1/chat/completions"
MODEL = "deepseek-chat"

# Google Books setup
GOOGLE_BOOKS_URL = "https://www.googleapis.com/books/v1/volumes"

def call_deepseek_api(series_name: str, volume: int) -> dict:
    """Call DeepSeek API for book info"""
    prompt = f"""
    Perform grounded deep research for the manga series "{series_name}" volume {volume}.
    Provide comprehensive information in JSON format with the following fields:

    Required fields:
    - series_name: The official series name
    - volume_number: {volume}
    - book_title: The specific title for this volume (append "(Volume {volume})")
    - authors: List of authors/artists in "Last, First M." format, comma-separated for multiple
    - msrp_cost: Manufacturer's Suggested Retail Price in USD
    - isbn_13: ISBN-13 for paperback English edition (preferred) or other available edition
    - publisher_name: Publisher of the English edition
    - copyright_year: 4-digit copyright year
    - description: Summary of the book's content and notable reviews
    - physical_description: Physical characteristics (pages, dimensions, etc.)
    - genres: List of genres/subjects
    - cover_image_url: Direct URL to the book's cover image from an authoritative source (publisher website, Amazon, etc.) if available

    Format requirements:
    - Shift leading articles to end ("The Last of the Mohicans" → "Last of the Mohicans, The")
    - Format author names as "Last, First M."
    - Use authoritative sources where possible
    - If information is unavailable, use best available data and note any gaps
    - Return only valid JSON, no additional text

    Example format:
    {{
      "series_name": "One Piece",
      "volume_number": 1,
      "book_title": "One Piece (Volume 1)",
      "authors": ["Oda, Eiichiro"],
      "msrp_cost": 9.99,
      "isbn_13": "9781569319017",
      "publisher_name": "VIZ Media LLC",
      "copyright_year": 2003,
      "description": "Monkey D. Luffy begins his journey...",
      "physical_description": "208 pages, 5 x 7.5 inches",
      "genres": ["Shonen", "Adventure", "Fantasy"],
      "cover_image_url": "https://www.viz.com/sites/default/files/one_piece_vol_1.jpg"
    }}
    """.strip()

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
    }

    payload = {
        "model": MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 1200,
        "temperature": 0.1,
    }

    try:
        response = requests.post(DEEPSEEK_URL, headers=headers, json=payload, timeout=60, verify=False)
        response.raise_for_status()

        result = response.json()
        content = result["choices"][0]["message"]["content"]

        # Parse JSON
        book_data = json.loads(content)
        return book_data, None

    except Exception as e:
        return None, str(e)

def call_google_books_api(isbn: str) -> str:
    from google_books_client import get_cover_image_url
    return get_cover_image_url(isbn)
    """Call Google Books API for cover image"""
    if not isbn:
        return None

    params = {"q": f"isbn:{isbn}"}

    try:
        response = requests.get(GOOGLE_BOOKS_URL, params=params, timeout=10)
        response.raise_for_status()

        data = response.json()

        if data.get("totalItems", 0) == 0:
            return None

        item = data["items"][0]
        volume_info = item.get("volumeInfo", {})
        image_links = volume_info.get("imageLinks", {})

        # Prefer larger images
        for size in ["extraLarge", "large", "medium", "small", "thumbnail"]:
            if size in image_links:
                return image_links[size]

        return None

    except Exception as e:
        print(f"Google Books error for ISBN {isbn}: {e}")
        return None

def main():
    # Test series
    test_series = [
        ("One Piece", 1),
        ("Naruto", 1),
        ("Bleach", 1),
        ("Death Note", 1),
        ("Dragon Ball", 1),
    ]

    # Create table
    db = sqlite3.connect("project_state.db")
    cursor = db.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS cover_comparison_results (
            id INTEGER PRIMARY KEY,
            series_name TEXT,
            volume INTEGER,
            deepseek_cover TEXT,
            google_cover TEXT,
            isbn TEXT,
            deepseek_success BOOLEAN,
            google_success BOOLEAN,
            deepseek_error TEXT,
            google_error TEXT,
            timestamp TEXT
        )
    """)
    db.commit()

    for series_name, volume in test_series:
        print(f"\nTesting {series_name} Volume {volume}")

        # Call DeepSeek
        deepseek_data, deepseek_error = call_deepseek_api(series_name, volume)

        deepseek_cover = None
        isbn = None
        deepseek_success = False

        if deepseek_data:
            deepseek_cover = deepseek_data.get("cover_image_url")
            isbn = deepseek_data.get("isbn_13")
            deepseek_success = True
            print(f"✓ DeepSeek: Cover={bool(deepseek_cover)}, ISBN={isbn}")
        else:
            print(f"✗ DeepSeek failed: {deepseek_error}")

        # Call Google Books
        google_cover = None
        google_success = False
        google_error = None

        if isbn:
            google_cover = call_google_books_api(isbn)  # Now downloads and returns local URL
            google_success = google_cover is not None
            print(f"✓ Google: Cover={bool(google_cover)}")
        else:
            google_error = "No ISBN from DeepSeek"
            print("✗ Google: No ISBN available")

        # Save to DB
        cursor.execute("""
            INSERT INTO cover_comparison_results 
            (series_name, volume, deepseek_cover, google_cover, isbn, deepseek_success, google_success, deepseek_error, google_error, timestamp)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (series_name, volume, deepseek_cover, google_cover, isbn, deepseek_success, google_success, deepseek_error, google_error, datetime.now().isoformat()))

        db.commit()

        # Rate limiting
        time.sleep(2)

    db.close()
    print("\nTest completed! Check the Flask app at http://localhost:5001")

if __name__ == "__main__":
    main()
