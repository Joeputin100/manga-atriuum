#!/usr/bin/env python3
"""
Fill Missing Volume Covers with Series Covers

This script updates the database to use series-level covers (from MangaDex)
for volumes that don't have individual covers.
"""

import json
import sqlite3


def get_all_volumes() -> list[dict]:
    """Get all volumes with their data from project_state.json"""
    try:
        with open("project_state.json") as f:
            state = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return []

    volumes = []
    for api_call in state.get("api_calls", []):
        if api_call.get("success", False):
            try:
                response = json.loads(api_call["response"])
                isbn = response.get("isbn_13")
                series = response.get("series_name")
                volume_num = api_call.get("volume")
                if isbn and series and volume_num:
                    volumes.append({
                        "series_name": series,
                        "volume_number": volume_num,
                        "isbn_13": isbn,
                        "cover_image_url": response.get("cover_image_url"),
                    })
            except json.JSONDecodeError:
                continue
    return volumes

def get_series_cover(series_name: str) -> str | None:
    """Get cached series cover URL from database"""
    db = sqlite3.connect("project_state.db")
    cursor = db.cursor()

    cursor.execute("SELECT url FROM cached_cover_images WHERE isbn = ?", (f"mangadex:{series_name}",))
    row = cursor.fetchone()

    db.close()
    return row[0] if row else None

def update_volume_cover(isbn: str, cover_url: str):
    """Update volume cover in database"""
    db = sqlite3.connect("project_state.db")
    cursor = db.cursor()

    cursor.execute("""
        INSERT OR REPLACE INTO cached_cover_images (isbn, url, timestamp)
        VALUES (?, ?, datetime('now'))
    """, (isbn, cover_url))

    db.commit()
    db.close()

def main():
    """Fill missing volume covers with series covers"""
    print("🔄 Filling missing volume covers with series covers...")

    volumes = get_all_volumes()
    print(f"Found {len(volumes)} volumes")

    updated_count = 0

    for volume in volumes:
        series = volume["series_name"]
        isbn = volume["isbn_13"]
        existing_cover = volume.get("cover_image_url")

        # Skip if already has a cover
        if existing_cover:
            continue

        # Get series cover
        series_cover = get_series_cover(series)
        if series_cover:
            update_volume_cover(isbn, series_cover)
            updated_count += 1
            print(f"✓ Updated {series} Vol. {volume['volume_number']} with series cover")
        else:
            print(f"✗ No series cover found for {series}")

    print(f"\n🎉 Updated {updated_count} volume covers with series fallbacks")

if __name__ == "__main__":
    main()
