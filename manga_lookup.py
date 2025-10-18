#!/usr/bin/env python3
import sqlite3
"""
Manga Lookup Tool

A comprehensive Python script that uses DeepSeek API for manga series lookup,
corrects series names, fetches detailed book information, and displays results
in an interactive Rich TUI with clickable row interface.
"""

import os
import json
import re
import time
import requests
import tomllib
from datetime import datetime
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from dotenv import load_dotenv
from rich.console import Console
from rich.prompt import Prompt, Confirm, IntPrompt
from rich.panel import Panel
from rich import print as rprint

# Load environment variables
load_dotenv()

@dataclass
class BookInfo:
    """Data class to store comprehensive book information"""
    series_name: str
    volume_number: int
    book_title: str
    authors: List[str]
    msrp_cost: Optional[float]
    isbn_13: Optional[str]
    publisher_name: Optional[str]
    copyright_year: Optional[int]
    description: Optional[str]
    physical_description: Optional[str]
    genres: List[str]
    warnings: List[str]
    barcode: Optional[str] = None
    cover_image_url: Optional[str] = None

class ProjectState:
    """Advanced project state management with SQLite database for performance"""

    def __init__(self, db_file="project_state.db"):
        self.db_file = db_file
        self.conn = sqlite3.connect(self.db_file, check_same_thread=False)
        self._create_tables()
        self._ensure_metadata()

    def _create_tables(self):
        """Create database tables if they don't exist"""
        cursor = self.conn.cursor()

        # Metadata table for global stats
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS metadata (
                key TEXT PRIMARY KEY,
                value TEXT
            )
        ''')

        # Cached responses table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS cached_responses (
                id INTEGER PRIMARY KEY,
                prompt_hash TEXT,
                volume INTEGER,
                response TEXT,
                timestamp TEXT,
                UNIQUE(prompt_hash, volume)
            )
        ''')

        # API calls table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS api_calls (
                id INTEGER PRIMARY KEY,
                prompt TEXT,
                response TEXT,
                volume INTEGER,
                success BOOLEAN,
                timestamp TEXT
            )
        ''')

        # Searches table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS searches (
                id INTEGER PRIMARY KEY,
                query TEXT,
                books_found INTEGER,
                timestamp TEXT
            )
        ''')

        # Cached cover images
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS cached_cover_images (
                id INTEGER PRIMARY KEY,
                isbn TEXT UNIQUE,
                url TEXT,
                timestamp TEXT
            )
        ''')

        self.conn.commit()

    def _ensure_metadata(self):
        """Ensure default metadata exists"""
        cursor = self.conn.cursor()
        defaults = {
            "interaction_count": "0",
            "total_books_found": "0",
            "start_time": datetime.now().isoformat()
        }
        for key, value in defaults.items():
            cursor.execute('INSERT OR IGNORE INTO metadata (key, value) VALUES (?, ?)', (key, value))
        self.conn.commit()

    def _get_metadata(self, key: str) -> str:
        cursor = self.conn.cursor()
        cursor.execute('SELECT value FROM metadata WHERE key = ?', (key,))
        row = cursor.fetchone()
        return row[0] if row else "0"

    def _set_metadata(self, key: str, value: str):
        cursor = self.conn.cursor()
        cursor.execute('INSERT OR REPLACE INTO metadata (key, value) VALUES (?, ?)', (key, value))
        self.conn.commit()

    def record_api_call(self, prompt: str, response: str, volume: int, success: bool = True):
        """Record API call with full details for caching"""
        cursor = self.conn.cursor()
        timestamp = datetime.now().isoformat()

        # Insert API call
        cursor.execute('''
            INSERT INTO api_calls (prompt, response, volume, success, timestamp)
            VALUES (?, ?, ?, ?, ?)
        ''', (prompt, response, volume, success, timestamp))

        # Cache successful responses
        if success:
            prompt_hash = f"{prompt[:100]}_{volume}"
            cursor.execute('''
                INSERT OR REPLACE INTO cached_responses (prompt_hash, volume, response, timestamp)
                VALUES (?, ?, ?, ?)
            ''', (prompt_hash, volume, response, timestamp))

        self.conn.commit()

    def get_cached_response(self, prompt: str, volume: int) -> Optional[str]:
        """Get cached response if available"""
        cursor = self.conn.cursor()
        prompt_hash = f"{prompt[:100]}_{volume}"
        cursor.execute('SELECT response FROM cached_responses WHERE prompt_hash = ? AND volume = ?', (prompt_hash, volume))
        row = cursor.fetchone()
        return row[0] if row else None

    def record_interaction(self, search_query: str, books_found: int):
        """Record a new user interaction"""
        cursor = self.conn.cursor()
        timestamp = datetime.now().isoformat()

        # Update metadata
        interaction_count = int(self._get_metadata("interaction_count")) + 1
        total_books = int(self._get_metadata("total_books_found")) + books_found
        self._set_metadata("interaction_count", str(interaction_count))
        self._set_metadata("total_books_found", str(total_books))

        # Insert search
        cursor.execute('INSERT INTO searches (query, books_found, timestamp) VALUES (?, ?, ?)',
                       (search_query, books_found, timestamp))
        self.conn.commit()

    def get_cached_cover_image(self, isbn_key: str) -> Optional[str]:
        """Get cached cover image URL by ISBN key"""
        cursor = self.conn.cursor()
        cursor.execute("SELECT url FROM cached_cover_images WHERE isbn = ?", (isbn_key,))
        row = cursor.fetchone()
        return row[0] if row else None

    def cache_cover_image(self, isbn_key: str, url: str):
        """Cache a cover image URL"""
        cursor = self.conn.cursor()
        timestamp = datetime.now().isoformat()
        cursor.execute("INSERT OR REPLACE INTO cached_cover_images (isbn, url, timestamp) VALUES (?, ?, ?)",
                       (isbn_key, url, timestamp))
        self.conn.commit()

class DeepSeekAPI:
    """Handles DeepSeek API interactions with rate limiting and error handling"""

    def __init__(self):
        self.api_key = os.getenv("DEEPSEEK_API_KEY")
        if not self.api_key:
            raise ValueError("DEEPSEEK_API_KEY not found in environment variables")

        self.base_url = "https://api.deepseek.com/v1/chat/completions"
        self.model = "deepseek-chat"  # Using DeepSeek-V3.2-Exp (non-thinking mode)
        self.last_request_time = time.time()

    def correct_series_name(self, series_name: str) -> List[str]:
        """Use DeepSeek API to correct and suggest manga series names"""
        prompt = f"""
        Given the manga series name "{series_name}", provide 3-5 corrected or alternative names
        that are actual manga series or editions.
        that are actual manga series.

        IMPORTANT: If "{series_name}" is already a correct manga series name, include it as the first suggestion.
        If "{series_name}" is a valid manga series, prioritize it over other suggestions.
        For popular series with multiple editions, include different formats:
        - Regular edition (individual volumes)
        - Omnibus edition (3 volumes per book)
        - Colossal edition (5 volumes per book)
        Format edition names as "Series Name (Edition Type)"

        Only include actual manga series names, not unrelated popular series.
        If "{series_name}" is misspelled or incomplete, provide the correct full name first.

        Prioritize the main series over spinoffs, sequels, or adaptations.
        If the series has multiple parts (like Tokyo Ghoul and Tokyo Ghoul:re), include the main series first.
        Include recent and ongoing series, not just completed ones.

        Return only the names as a JSON list, no additional text.

        Example format: ["Attack on Titan (Regular Edition)", "Attack on Titan (Omnibus Edition)", "Attack on Titan (Colossal Edition)", "One Piece", "Naruto"]
        """

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }

        payload = {
            "model": self.model,
            "messages": [
                {"role": "user", "content": prompt}
            ],
            "max_tokens": 200,
            "temperature": 0.3
        }

        content = None  # Initialize content variable

        try:
            response = requests.post(self.base_url, headers=headers, json=payload, timeout=60)
            response.raise_for_status()

            result = response.json()
            content = result["choices"][0]["message"]["content"]

            # Debug logging
            print(f"DEBUG: DeepSeek API response status: {response.status_code}")
            print(f"DEBUG: DeepSeek API response content: {content}")

            # Parse JSON response
            suggestions = json.loads(content)

            # Filter out any None values from suggestions
            suggestions = [s for s in suggestions if s is not None]

            # Debug logging
            print(f"DEBUG: Filtered suggestions: {suggestions}")

            # Ensure the original series name is included if it's valid
            # Check if the original name is in the suggestions, if not add it
            if series_name not in suggestions:
                # Check if any suggestion contains the original name (case-insensitive)
                original_in_suggestions = any(
                    suggestion and series_name.lower() in suggestion.lower()
                    for suggestion in suggestions
                )
                if not original_in_suggestions:
                    # Add original name as first suggestion
                    suggestions.insert(0, series_name)

            return suggestions

        except json.JSONDecodeError as e:
            rprint(f"[red]JSON decode error in DeepSeek API response: {e}[/red]")
            rprint(f"[yellow]Response content: {content if content else 'Not available'}[/yellow]")
            return [series_name]  # Fallback to original name
        except Exception as e:
            rprint(f"[red]Error using DeepSeek API: {e}[/red]")
            return [series_name]  # Fallback to original name

    def get_book_info(self, series_name: str, volume_number: int, project_state: ProjectState) -> Optional[Dict]:
        """Get comprehensive book information using DeepSeek API"""

        # Create comprehensive prompt
        prompt = self._create_comprehensive_prompt(series_name, volume_number)

        # Check cache first
        cached_response = project_state.get_cached_response(prompt, volume_number)
        if cached_response:
            rprint(f"[cyan]📚 Using cached data for volume {volume_number}[/cyan]")
            try:
                return json.loads(cached_response)
            except json.JSONDecodeError:
                rprint(f"[yellow]⚠️ Cached data corrupted, fetching fresh data[/yellow]")

        # If we get here, we need to make a new API call
        rprint(f"[blue]🔍 Making API call for volume {volume_number}[/blue]")

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }

        payload = {
            "model": self.model,
            "messages": [
                {"role": "user", "content": prompt}
            ],
            "max_tokens": 1000,
            "temperature": 0.1
        }

        try:
            response = requests.post(self.base_url, headers=headers, json=payload, timeout=120)
            response.raise_for_status()

            result = response.json()
            content = result["choices"][0]["message"]["content"]
            # Parse JSON response
            content = content.strip()
            if content.startswith('```json'):
                content = content[7:]
            if content.endswith('```'):
                content = content[:-3]
            content = content.strip()
            try:
                book_data = json.loads(content)
            except json.JSONDecodeError as e:

                rprint(f"[red]Invalid JSON response for volume {volume_number}: {e}[/red]")
                rprint(f"[red]Content: {content[:500]}[/red]")
                project_state.record_api_call(prompt, content, volume_number, success=False)
            if not book_data.get('number_of_extant_volumes'):
                google_api = GoogleBooksAPI()
                book_data['number_of_extant_volumes'] = google_api.get_total_volumes(series_name)
                return None

            # Record successful API call
            project_state.record_api_call(prompt, content, volume_number, success=True)

            return book_data

        except requests.exceptions.HTTPError as e:
            if e.response and e.response.status_code == 429:
                rprint(f"[yellow]Rate limit exceeded for volume {volume_number}, waiting 5 seconds...[/yellow]")
                time.sleep(5)
                return self.get_book_info(series_name, volume_number, project_state)
            else:
                rprint(f"[red]HTTP error for volume {volume_number}: {e}[/red]")
        except Exception as e:
            rprint(f"[red]Error fetching data for volume {volume_number}: {e}[/red]")
            return None
class VertexAPI:
    """Handles Vertex AI interactions using Gemini model"""

    def __init__(self):
        self.api_key = os.getenv("GEMINI_API_KEY")
        self.base_url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent"
        self.model = "gemini-1.5-flash"

    def get_book_info(self, series_name: str, volume_number: int, project_state: ProjectState) -> Optional[Dict]:
        """Get comprehensive book information using Vertex AI"""

        # Create comprehensive prompt
        prompt = self._create_comprehensive_prompt(series_name, volume_number)

        # Check cache first
        cached_response = project_state.get_cached_response(prompt, volume_number)
        if cached_response:
            rprint(f"[cyan]📚 Using cached data from Vertex for volume {volume_number}[/cyan]")
            try:
                return json.loads(cached_response)
            except json.JSONDecodeError:
                rprint(f"[yellow]⚠️ Cached data corrupted, fetching fresh data[/yellow]")

        # If we get here, we need to make a new API call
        rprint(f"[blue]🔍 Making Vertex API call for volume {volume_number}[/blue]")

        url = f"{self.base_url}?key={self.api_key}" if self.api_key else self.base_url

        payload = {
            "contents": [
                {
                    "parts": [
                        {
                            "text": prompt
                        }
                    ]
                }
            ]
        }

        try:
            response = requests.post(url, json=payload, timeout=120)
            response.raise_for_status()

            result = response.json()
            content = result["candidates"][0]["content"]["parts"][0]["text"]

            # Strip markdown if present
            content = content.strip()
            if content.startswith('```json'):
                content = content[7:]
            if content.endswith('```'):
                content = content[:-3]
            content = content.strip()

            # Parse JSON response
            try:
                book_data = json.loads(content)
            except json.JSONDecodeError as e:
                rprint(f"[red]Invalid JSON response from Vertex for volume {volume_number}: {e}[/red]")
                rprint(f"[red]Content: {content[:500]}[/red]")
                project_state.record_api_call(prompt, content, volume_number, success=False)
                return None

            # Record successful API call
            project_state.record_api_call(prompt, content, volume_number, success=True)

            return book_data

        except requests.exceptions.HTTPError as e:
            rprint(f"[red]HTTP error from Vertex for volume {volume_number}: {e}[/red]")
            project_state.record_api_call(prompt, str(e), volume_number, success=False)
            return None
        except Exception as e:
            rprint(f"[red]Error fetching data from Vertex for volume {volume_number}: {e}[/red]")
            project_state.record_api_call(prompt, str(e), volume_number, success=False)
            return None

    def _create_comprehensive_prompt(self, series_name: str, volume_number: int) -> str:
        """Create a comprehensive prompt for Vertex AI"""
        # Determine edition and volume_text
        if "omnibus" in series_name.lower():
            edition_type = "omnibus"
            volumes_per_book = 3
            volume_text = f"{volume_number * 3 - 2}-{volume_number * 3}"
        elif "colossal" in series_name.lower():
            edition_type = "colossal"
            volumes_per_book = 5
            volume_text = f"{volume_number * 5 - 4}-{volume_number * 5}"
        else:
            edition_type = "regular"
            volumes_per_book = 1
            volume_text = str(volume_number)

        return f"""
        Perform grounded deep research for the manga series "{series_name}" volume {volume_number}.
        Provide comprehensive information in JSON format with the following fields:

        Required fields:
        - series_name: The official series name
        - volume_number: {volume_number}
        - book_title: The specific title for this volume (append "(Volume {volume_text})")
        - volume_text: The volume number or range for this book (e.g., "1" for regular, "1-3" for omnibus, "1-5" for colossal)
        - authors: List of authors/artists in "Last, First M." format, comma-separated for multiple
        - msrp_cost: Manufacturer's Suggested Retail Price in USD
        - isbn_13: ISBN-13 for paperback English edition (preferred) or other available edition
        - publisher_name: Publisher of the English edition
        - copyright_year: 4-digit copyright year
        - description: Summary of the book's content and notable reviews
        - physical_description: Physical characteristics (pages, dimensions, etc.)
        - genres: List of genres/subjects
        - number_of_extant_volumes: Total number of volumes published for this series
        - edition_type: Type of edition (regular, omnibus, colossal)
        - volumes_per_book: Number of volumes per book for this edition

        Provide the information as valid JSON that can be parsed.
        """
