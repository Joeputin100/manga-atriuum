#!/usr/bin/env python3
"""
Cover Image Comparison Test

Compares cover image URLs from DeepSeek API vs Google Books API (keyless)
for 100 popular manga volumes.
"""

import os
import json
import time
import requests
from typing import Dict, List, Optional, Tuple
from datetime import datetime
import sqlite3
from dotenv import load_dotenv

# Load environment
load_dotenv()

# Import our modules
from manga_lookup import DeepSeekAPI, GoogleBooksAPI, ProjectState
from test_manga_list import TEST_MANGA

class CoverComparisonTester:
    """Test class for comparing cover image sources"""
    
    def __init__(self):
        self.deepseek_api = DeepSeekAPI()
        self.google_api = GoogleBooksAPI()
        self.project_state = ProjectState()
        self.results = []
        
    def test_single_volume(self, series_name: str, volume: int) -> Dict:
        """Test a single volume"""
        print(f"Testing {series_name} Volume {volume}")
        
        result = {
            'series_name': series_name,
            'volume': volume,
            'deepseek_cover': None,
            'google_cover': None,
            'isbn': None,
            'deepseek_success': False,
            'google_success': False,
            'timestamp': datetime.now().isoformat()
        }
        
        # Get data from DeepSeek
        try:
            deepseek_data = self.deepseek_api.get_book_info(series_name, volume, self.project_state)
            if deepseek_data:
                result['deepseek_cover'] = deepseek_data.get('cover_image_url')
                result['isbn'] = deepseek_data.get('isbn_13')
                result['deepseek_success'] = True
        except Exception as e:
            print(f"DeepSeek error for {series_name} {volume}: {e}")
        
        # Get cover from Google Books
        if result['isbn']:
            try:
                google_cover = self.google_api.get_cover_image_url(result['isbn'], project_state=self.project_state)
                if google_cover:
                    result['google_cover'] = google_cover
                    result['google_success'] = True
            except Exception as e:
                print(f"Google error for {series_name} {volume}: {e}")
        
        return result
    
    def run_tests(self, limit: int = 100) -> List[Dict]:
        """Run tests for all volumes"""
        test_volumes = TEST_MANGA[:limit]
        
        for series_name, volume in test_volumes:
            result = self.test_single_volume(series_name, volume)
            self.results.append(result)
            
            # Save to DB
            self.save_result_to_db(result)
            
            # Small delay to be respectful
            time.sleep(0.5)
        
        return self.results
    
    def save_result_to_db(self, result: Dict):
        """Save result to database"""
        cursor = self.project_state.conn.cursor()
        cursor.execute('''
            INSERT INTO cover_comparison_results 
            (series_name, volume, deepseek_cover, google_cover, isbn, deepseek_success, google_success, timestamp)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            result['series_name'],
            result['volume'],
            result['deepseek_cover'],
            result['google_cover'],
            result['isbn'],
            result['deepseek_success'],
            result['google_success'],
            result['timestamp']
        ))
        self.project_state.conn.commit()

def create_results_table():
    """Create results table if it doesn't exist"""
    db = sqlite3.connect('project_state.db')
    cursor = db.cursor()
    cursor.execute('''
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
    ''')
    db.commit()
    db.close()

if __name__ == "__main__":
    # Create results table
    create_results_table()
    
    # Run tests
    tester = CoverComparisonTester()
    results = tester.run_tests(10)  # Limit for testing
    
    print(f"Completed testing {len(results)} volumes")
    
    # Summary
    deepseek_success = sum(1 for r in results if r['deepseek_success'])
    google_success = sum(1 for r in results if r['google_success'])
    both_success = sum(1 for r in results if r['deepseek_success'] and r['google_success'])
    
    print(f"DeepSeek covers found: {deepseek_success}")
    print(f"Google covers found: {google_success}")
    print(f"Both found: {both_success}")
