#!/usr/bin/env python3
import random
import sqlite3
from datetime import datetime

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
        timestamp TEXT
    )
""")
db.commit()

# Test data
series_list = ["One Piece", "Naruto", "Bleach", "Dragon Ball", "Death Note"]

for i in range(10):
    series = random.choice(series_list)
    volume = random.randint(1, 5)
    deepseek_success = random.choice([True, False])
    google_success = random.choice([True, False])

    # Use picsum.photos for mock API URLs - different seeds for different sources
    deepseek_cover = f"https://picsum.photos/200/300?random={hash(series + 'DeepSeek') % 1000}" if deepseek_success else None
    google_cover = f"https://picsum.photos/200/300?random={hash(series + 'Google') % 1000}" if google_success else None
    isbn = f"978123456789{random.randint(0,9)}"

    cursor.execute("""
        INSERT INTO cover_comparison_results 
        (series_name, volume, deepseek_cover, google_cover, isbn, deepseek_success, google_success, timestamp)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (series, volume, deepseek_cover, google_cover, isbn, deepseek_success, google_success, datetime.now().isoformat()))

    print(f"Added test result for {series} Vol {volume}")

db.commit()
db.close()

print("Test data with mock API URLs added to database")
