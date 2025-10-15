#!/usr/bin/env python3
"""
Cover Image Comparison Test (Mocked)

Compares cover image URLs from DeepSeek API vs Google Books API (keyless)
for 100 popular manga volumes. Using mock data for testing.
"""

import os
import json
import time
import random
from typing import Dict, List, Optional, Tuple
from datetime import datetime
import sqlite3

# Import our modules
from typing import Dict, List
from test_manga_list import TEST_MANGA

class CoverComparisonTester:
    """Test class for comparing cover image sources"""
    
    def __init__(self):
        self.project_state = ProjectState()
        self.results = []
        
    def test_single_volume(self, series_name: str, volume: int) -> Dict:
        """Test a single volume (mocked for testing)"""
        result = {
            'series_name': series_name,
            'volume': volume,
            'deepseek_cover': None,
            'google_cover': None,
            'isbn': f"978123456789{random.randint(0,9)}",
            'deepseek_success': random.choice([True, False]),
            'google_success': random.choice([True, False]),
            'timestamp': datetime.now().isoformat()
        }
        
        if result['deepseek_success']:
            result['deepseek_cover'] = f"https://via.placeholder.com/200x300?text={series_name.replace(' ', '%20')}+DeepSeek"
        
        if result['google_success']:
            result['google_cover'] = f"https://via.placeholder.com/200x300?text={series_name.replace(' ', '%20')}+Google"
        
        return result
    
    def run_tests(self, limit: int = 100) -> List[Dict]:
        """Run tests for all volumes"""
        test_volumes = TEST_MANGA[:limit]
        
        for series_name, volume in test_volumes:
            result = self.test_single_volume(series_name, volume)
            self.results.append(result)
            
            # Save to DB
            self.save_result_to_db(result)
            
            # Small delay to simulate API calls
            time.sleep(0.1)
        
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
    results = tester.run_tests(10)  # Test with 10 for speed
    
    print(f"Completed testing {len(results)} volumes")
    
    # Summary
    deepseek_success = sum(1 for r in results if r['deepseek_success'])
    google_success = sum(1 for r in results if r['google_success'])
    both_success = sum(1 for r in results if r['deepseek_success'] and r['google_success'])
    
    print(f"DeepSeek covers found: {deepseek_success}")
    print(f"Google covers found: {google_success}")
    print(f"Both found: {both_success}")
