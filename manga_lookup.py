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

class DataValidator:
    """Handles data validation and formatting"""

    @staticmethod
    def format_title(title: str) -> str:
        """Format title with leading articles shifted to the end"""
        articles = ["the", "a", "an"]
        words = title.split()

        if words and words[0].lower() in articles:
            article = words[0]
            rest = " ".join(words[1:])
            return f"{rest}, {article.capitalize()}"

        return title

    @staticmethod
    def format_author_name(author_name: str) -> str:
        """Format author name as 'Last, First M.'"""
        if not author_name:
            return ""

        # Check if already in "Last, First" format
        if ", " in author_name:
            return author_name

        # Handle common Japanese name formats
        name_parts = author_name.strip().split()

        if len(name_parts) == 2:
            # Assume "First Last" format
            return f"{name_parts[1]}, {name_parts[0]}"
        elif len(name_parts) == 1:
            # Single name (like "Oda")
            return name_parts[0]
        else:
            # Complex name, try to handle
            if any(part.endswith('-') for part in name_parts):
                # Handle hyphenated names
                return author_name
            else:
                # Default: assume first part is first name, last part is last name
                return f"{name_parts[-1]}, {' '.join(name_parts[:-1])}"

    @staticmethod
    def format_authors_list(authors: List[str]) -> str:
        """Format list of authors as comma-separated 'Last, First M.'"""
        if not authors:
            return ""
        formatted_authors = [DataValidator.format_author_name(author) for author in authors]
        return ", ".join(formatted_authors)

def parse_volume_range(volume_input: str) -> List[int]:
    """Parse volume range input like '1-5,7,10' and omnibus formats like '17-18-19' into list of volume numbers"""
    volumes = []

    # Split by commas
    parts = [part.strip() for part in volume_input.split(",")]

    for part in parts:
        if '-' in part:
            # Count the number of hyphens to determine format
            hyphens_count = part.count('-')

            if hyphens_count == 1:
                # Handle range like '1-5' (single range)
                try:
                    start, end = map(int, part.split('-'))
                    volumes.extend(range(start, end + 1))
                except ValueError:
                    raise ValueError(f"Invalid volume range format: {part}")
            else:
                # Handle omnibus format like '17-18-19' (multiple volumes in one book)
                try:
                    # Split by hyphens and convert all parts to integers
                    omnibus_volumes = list(map(int, part.split('-')))
                    volumes.extend(omnibus_volumes)
                except ValueError:
                    raise ValueError(f"Invalid omnibus format: {part}")
        else:
            # Handle single volume like '7'
            try:
                volumes.append(int(part))
            except ValueError:
                raise ValueError(f"Invalid volume number: {part}")

    # Remove duplicates and sort
    return sorted(list(set(volumes)))

class GoogleBooksAPI:
    """Handles Google Books API interactions for cover image retrieval using keyless queries"""

    def __init__(self):
        self.base_url = "https://www.googleapis.com/books/v1/volumes"
        self.api_key = os.getenv("GEMINI_API_KEY")

    def get_cover_image_url(self, isbn: str, project_state: Optional[ProjectState] = None) -> Optional[str]:
        if not isbn:
            return None

        # Check cache first if project_state is provided
        if project_state:
            cached_url = project_state.get_cached_cover_image(f"isbn:{isbn}")
            if cached_url:
                return cached_url

        # Construct the keyless API URL
        url = f"{self.base_url}?q=isbn:{isbn}&maxResults=1"
        if self.api_key:
            url += f"&key={self.api_key}"

        try:
            # Make the keyless HTTP request
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            data = response.json()

            if data.get('totalItems', 0) == 0:
                return None

            volume_info = data['items'][0]['volumeInfo']
            image_links = volume_info.get('imageLinks', {})

            # Get the small thumbnail cover image URL
            cover_url = image_links.get('smallThumbnail')

            # If small thumbnail not available, try other sizes
            if not cover_url:
                for size in ['thumbnail', 'small', 'medium', 'large', 'extraLarge']:
                    if size in image_links:
                        cover_url = image_links[size]
                        break

            if cover_url:
                if project_state:
                    project_state.cache_cover_image(f"isbn:{isbn}", cover_url)
            else:
                print(f"✗ No cover image found in Google Books for ISBN {isbn}")

            return cover_url

        except Exception as e:
            print(f"Error fetching cover image: {e}")
            return None

    def get_series_cover_image(self, series_name: str, volume_number: int = 1, project_state: Optional[ProjectState] = None) -> Optional[str]:
        # Check cache first if project_state is provided
        if project_state:
            cached_url = project_state.get_cached_cover_image(f"series:{series_name}")
            if cached_url:
                return cached_url
        
        # Search for the series with volume 1
        query = f'intitle:"{series_name}" "volume {volume_number}" manga'
        url = f"{self.base_url}?q={query}&maxResults=1"
        if self.api_key:
            url += f"&key={self.api_key}"
        
        try:
            # Make the keyless HTTP request
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            if data.get('totalItems', 0) == 0:
                return None
            
            volume_info = data['items'][0]['volumeInfo']
            image_links = volume_info.get('imageLinks', {})
            
            # Get the small thumbnail cover image URL
            cover_url = image_links.get('smallThumbnail')
            
            # If small thumbnail not available, try other sizes
            if not cover_url:
                for size in ['thumbnail', 'small', 'medium', 'large', 'extraLarge']:
                    if size in image_links:
                        cover_url = image_links[size]
                        break
            
            return cover_url
        
        except Exception as e:
            print(f"Error fetching series cover image: {e}")
            return None

    def get_total_volumes(self, series_name: str) -> int:
        """Get approximate total number of volumes for a series from Google Books API"""
        query = f'intitle:"{series_name}" manga'
        url = f"{self.base_url}?q={query}&maxResults=1"
        if self.api_key:
            url += f"&key={self.api_key}"
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            data = response.json()
            return data.get('totalItems', 0)
        except Exception as e:
            print(f"Error fetching total volumes from Google Books: {e}")
            return 0

    def get_book_info_from_google(self, series_name: str, volume_number: int) -> Optional[Dict]:
        """Fallback: Get basic book info from Google Books API"""
        query = f'intitle:"{series_name}" "volume {volume_number}" manga'
        url = f"{self.base_url}?q={query}&maxResults=1"
        if self.api_key:
            url += f"&key={self.api_key}"
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            data = response.json()
            if data.get('totalItems', 0) == 0:
                return None
            volume_info = data['items'][0]['volumeInfo']
            # Map to our format
            book_data = {
                'series_name': series_name,
                'volume_number': volume_number,
                'book_title': volume_info.get('title', f"{series_name} (Volume {volume_number})"),
                'authors': volume_info.get('authors', []),
                'description': volume_info.get('description', ''),
                'publisher_name': volume_info.get('publisher', ''),
                'copyright_year': volume_info.get('publishedDate', '').split('-')[0] if volume_info.get('publishedDate') else None,
                'physical_description': '',
                'genres': volume_info.get('categories', []),
                'isbn_13': None,
                'msrp_cost': None,
                'cover_image_url': None,
            }
            # Try to get ISBN
            identifiers = volume_info.get('industryIdentifiers', [])
            for ident in identifiers:
                if ident.get('type') == 'ISBN_13':
                    book_data['isbn_13'] = ident.get('identifier')
                    break
            # Try to get cover
            image_links = volume_info.get('imageLinks', {})
            cover_url = image_links.get('smallThumbnail') or image_links.get('thumbnail')
            book_data['cover_image_url'] = cover_url
            return book_data
        except Exception as e:
            print(f"Error fetching from Google Books: {e}")
            return None

def generate_sequential_barcodes(start_barcode: str, count: int) -> List[str]:
    """Generate sequential barcodes from a starting barcode"""
    barcodes = []

    # Extract prefix and numeric part
    import re
    match = re.match(r'([A-Za-z]*)(\d+)', start_barcode)

    if not match:
        raise ValueError(f"Invalid barcode format: {start_barcode}. Expected format like 'T000001'")

    prefix = match.group(1) or ""
    start_num = int(match.group(2))
    num_digits = len(match.group(2))

    for i in range(count):
        current_num = start_num + i
        barcode = f"{prefix}{current_num:0{num_digits}d}"
        barcodes.append(barcode)

    return barcodes

def process_book_data(raw_data: Dict, volume_number: int, google_books_api: Optional[GoogleBooksAPI] = None, project_state: Optional[ProjectState] = None) -> BookInfo:
    """Process raw API data into structured BookInfo"""
    warnings = []

    # Extract and validate data
    series_name = DataValidator.format_title(raw_data.get("series_name", ""))
    book_title = DataValidator.format_title(raw_data.get("book_title", f"{series_name} (Volume {volume_number})"))

    # Ensure series name is in the title if missing
    if series_name and series_name.lower() not in book_title.lower():
        book_title = f"{series_name}: {book_title}"

    # Handle authors - ensure they're in list format
    authors_raw = raw_data.get("authors", [])
    if isinstance(authors_raw, str):
        # Check if the string contains multiple authors separated by commas
        # Look for patterns that indicate multiple authors vs single author with comma
        if ", " in authors_raw:
            # Check if it's likely a single author in "Last, First" format
            parts = authors_raw.split(", ")
            if len(parts) == 2 and len(parts[0].split()) <= 2 and len(parts[1].split()) <= 2:
                # Likely a single author in "Last, First" format
                authors = [authors_raw.strip()]
            else:
                # Likely multiple authors, split by comma
                authors = [author.strip() for author in authors_raw.split(",")]
        else:
            # No commas, treat as single author
            authors = [authors_raw.strip()]
    else:
        authors = authors_raw

    # Validate MSRP
    msrp_cost = raw_data.get("msrp_cost")
    if msrp_cost is None:
        warnings.append("No MSRP found")
    else:
        try:
            msrp_cost = float(msrp_cost)
            if msrp_cost < 10:
                rounded_msrp = 10.0
                warnings.append(f"MSRP ${msrp_cost:.2f} is below minimum $10 (rounded up to ${rounded_msrp:.2f})")
            elif msrp_cost > 30:
                warnings.append(f"MSRP ${msrp_cost:.2f} exceeds typical maximum $30")
        except (ValueError, TypeError):
            warnings.append("Invalid MSRP format")
            msrp_cost = None

    # Validate copyright year
    copyright_year = None
    date_str = str(raw_data.get("copyright_year", ""))
    if date_str:
        import re
        year_patterns = [r'\b(19|20)\d{2}\b', r'\b\d{4}\b']
        for pattern in year_patterns:
            matches = re.findall(pattern, date_str)
            if matches:
                year = int(matches[0])
                if 1900 <= year <= datetime.now().year + 1:
                    copyright_year = year
                    break
    if not copyright_year:
        warnings.append("Could not extract valid copyright year")

    # Handle genres
    genres_raw = raw_data.get("genres", [])
    if isinstance(genres_raw, str):
        genres = [genre.strip() for genre in genres_raw.split(",")]
    else:
        genres = genres_raw

    # Extract cover image URL if available from DeepSeek data
    cover_image_url = raw_data.get("cover_image_url")

    # If no cover image from DeepSeek and Google Books API is available, try to fetch it
    if not cover_image_url and google_books_api:
        isbn = raw_data.get("isbn_13")
        if isbn:
            cover_image_url = google_books_api.get_cover_image_url(isbn, project_state=project_state)
            # Debug: Print cover image status
            if cover_image_url:
                print(f"✓ Found cover image for ISBN {isbn}: {cover_image_url}")
            else:
                print(f"✗ No cover image found for ISBN {isbn}")

    return BookInfo(
        series_name=series_name,
        volume_number=volume_number,
        book_title=book_title,
        authors=authors,
        msrp_cost=msrp_cost,
        isbn_13=raw_data.get("isbn_13"),
        publisher_name=raw_data.get("publisher_name"),
        copyright_year=copyright_year,
        description=raw_data.get("description"),
        physical_description=raw_data.get("physical_description"),
        genres=genres,
        warnings=warnings,
        cover_image_url=cover_image_url
    )
