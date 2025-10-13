#!/usr/bin/env python3
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

class ProjectState:
    """Advanced project state management with API call logging"""

    def __init__(self, state_file="project_state.json"):
        self.state_file = state_file
        self.state = self._load_state()

    def _load_state(self) -> Dict:
        """Load project state from JSON file"""
        if os.path.exists(self.state_file):
            try:
                with open(self.state_file, 'r') as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError) as e:
                rprint(f"[yellow]Warning: Could not load state file: {e}[/yellow]")

        # Default state
        return {
            "interaction_count": 0,
            "searches": [],
            "api_calls": [],
            "last_search": None,
            "total_books_found": 0,
            "cached_responses": {},
            "start_time": datetime.now().isoformat()
        }

    def save_state(self):
        """Save current state to JSON file"""
        try:
            with open(self.state_file, 'w') as f:
                json.dump(self.state, f, indent=2)
        except IOError as e:
            rprint(f"[red]Warning: Could not save project state: {e}[/red]")

    def record_api_call(self, prompt: str, response: str, volume: int, success: bool = True):
        """Record API call with full details for caching"""
        api_call = {
            "prompt": prompt,
            "response": response,
            "volume": volume,
            "success": success,
            "timestamp": datetime.now().isoformat()
        }
        self.state["api_calls"].append(api_call)

        # Cache successful responses
        if success:
            cache_key = f"{prompt[:100]}_{volume}"
            self.state["cached_responses"][cache_key] = response

        self.save_state()

    def get_cached_response(self, prompt: str, volume: int) -> Optional[str]:
        """Get cached response if available"""
        cache_key = f"{prompt[:100]}_{volume}"
        return self.state["cached_responses"].get(cache_key)

    def record_interaction(self, search_query: str, books_found: int):
        """Record a new user interaction"""
        self.state["interaction_count"] += 1
        self.state["total_books_found"] += books_found

        search_record = {
            "query": search_query,
            "books_found": books_found,
            "timestamp": datetime.now().isoformat()
        }
        self.state["searches"].append(search_record)
        self.state["last_search"] = search_record

        self.save_state()

class DeepSeekAPI:
    """Handles DeepSeek API interactions with rate limiting and error handling"""

    def __init__(self):
        self.api_key = os.getenv("DEEPSEEK_API_KEY")
        if not self.api_key:
            raise ValueError("DEEPSEEK_API_KEY not found in environment variables")

        self.base_url = "https://api.deepseek.com/v1/chat/completions"
        self.model = "deepseek-chat"  # Using DeepSeek-V3.2-Exp (non-thinking mode)
        self.last_request_time = 0
        self.min_request_interval = 1  # 1 second between requests

    def _rate_limit(self):
        """Implement basic rate limiting"""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time

        if time_since_last < self.min_request_interval:
            time.sleep(self.min_request_interval - time_since_last)

        self.last_request_time = time.time()

    def correct_series_name(self, series_name: str) -> List[str]:
        """Use DeepSeek API to correct and suggest manga series names"""
        self._rate_limit()

        prompt = f"""
        Given the manga series name "{series_name}", provide 3-5 corrected or alternative names
        that are actual manga series.

        IMPORTANT: If "{series_name}" is already a correct manga series name, include it as the first suggestion.
        If "{series_name}" is a valid manga series, prioritize it over other suggestions.

        Only include actual manga series names, not unrelated popular series.
        If "{series_name}" is misspelled or incomplete, provide the correct full name first.

        Prioritize the main series over spinoffs, sequels, or adaptations.
        If the series has multiple parts (like Tokyo Ghoul and Tokyo Ghoul:re), include the main series first.
        Include recent and ongoing series, not just completed ones.
        For Boruto specifically, include both "Boruto: Naruto Next Generations" and "Boruto: Two Blue Vortex".

        Return only the names as a JSON list, no additional text.

        Example format: ["One Piece", "Naruto", "Bleach", "Boruto: Naruto Next Generations", "Boruto: Two Blue Vortex"]
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

        try:
            response = requests.post(self.base_url, headers=headers, json=payload, timeout=60)
            response.raise_for_status()

            result = response.json()
            content = result["choices"][0]["message"]["content"]

            # Parse JSON response
            suggestions = json.loads(content)

            # Ensure the original series name is included if it's valid
            # Check if the original name is in the suggestions, if not add it
            if series_name not in suggestions:
                # Check if any suggestion contains the original name (case-insensitive)
                original_in_suggestions = any(
                    series_name.lower() in suggestion.lower()
                    for suggestion in suggestions
                )
                if not original_in_suggestions:
                    # Add original name as first suggestion
                    suggestions.insert(0, series_name)

            return suggestions

        except Exception as e:
            rprint(f"[red]Error using DeepSeek API: {e}[/red]")
            return [series_name]  # Fallback to original name

    def get_book_info(self, series_name: str, volume_number: int, project_state: ProjectState) -> Optional[Dict]:
        """Get comprehensive book information using DeepSeek API"""
        self._rate_limit()

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
            book_data = json.loads(content)

            # Record successful API call
            project_state.record_api_call(prompt, content, volume_number, success=True)

            return book_data

        except Exception as e:
            rprint(f"[red]Error fetching data for volume {volume_number}: {e}[/red]")
            project_state.record_api_call(prompt, str(e), volume_number, success=False)
            return None

    def _create_comprehensive_prompt(self, series_name: str, volume_number: int) -> str:
        """Create a comprehensive prompt for DeepSeek API"""
        return f"""
        Perform grounded deep research for the manga series "{series_name}" volume {volume_number}.
        Provide comprehensive information in JSON format with the following fields:

        Required fields:
        - series_name: The official series name
        - volume_number: {volume_number}
        - book_title: The specific title for this volume (append "(Volume {volume_number})")
        - authors: List of authors/artists in "Last, First M." format, comma-separated for multiple
        - msrp_cost: Manufacturer's Suggested Retail Price in USD
        - isbn_13: ISBN-13 for paperback English edition (preferred) or other available edition
        - publisher_name: Publisher of the English edition
        - copyright_year: 4-digit copyright year
        - description: Summary of the book's content and notable reviews
        - physical_description: Physical characteristics (pages, dimensions, etc.)
        - genres: List of genres/subjects

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
          "genres": ["Shonen", "Adventure", "Fantasy"]
        }}
        """.strip()

    def _get_series_info(self, series_name: str) -> Optional[str]:
        """Get brief information about a manga series for display"""
        self._rate_limit()

        prompt = f"""
        Provide a brief one-line description of the manga series "{series_name}"
        including the author and main genre. Keep it very concise (max 60 characters).

        Examples:
        - "One Piece" → "Eiichiro Oda, Shonen Adventure"
        - "Tokyo Ghoul" → "Sui Ishida, Dark Fantasy Horror"
        - "Naruto" → "Masashi Kishimoto, Shonen Ninja"

        Return only the description text, no additional formatting.
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
            "max_tokens": 100,
            "temperature": 0.1
        }

        try:
            response = requests.post(self.base_url, headers=headers, json=payload, timeout=30)
            response.raise_for_status()

            result = response.json()
            content = result["choices"][0]["message"]["content"].strip()

            # Limit to 60 characters for display
            if len(content) > 60:
                content = content[:57] + "..."

            return content

        except Exception:
            # If we can't get info, just return None
            return None

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


def process_book_data(raw_data: Dict, volume_number: int) -> BookInfo:
    """Process raw API data into structured BookInfo"""
    warnings = []

    # Extract and validate data
    series_name = DataValidator.format_title(raw_data.get("series_name", ""))
    book_title = DataValidator.format_title(raw_data.get("book_title", f"{series_name} (Volume {volume_number})"))

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
        warnings=warnings
    )

def display_text_list(books: List[BookInfo], console: Console):
    """Display books in a text-based list with field status indicators and barcodes"""

    console.print(f"\n[bold blue]Manga Series Results ({len(books)} books found)[/bold blue]")
    console.print("=" * 80)

    # Display the list
    for i, book in enumerate(books, 1):
        formatted_authors = DataValidator.format_authors_list(book.authors)

        # Show basic info with barcode
        console.print(f"\n[bold]{i}. Volume {book.volume_number}: {book.book_title}[/bold]")
        console.print(f"   Authors: {formatted_authors}")
        console.print(f"   Barcode: [cyan]{book.barcode}[/cyan]")

        # Show field status indicators
        status_fields = [
            ("MSRP", book.msrp_cost is not None),
            ("ISBN-13", bool(book.isbn_13)),
            ("Publisher", bool(book.publisher_name)),
            ("Copyright Year", book.copyright_year is not None),
            ("Description", bool(book.description)),
            ("Physical Description", bool(book.physical_description)),
            ("Genres", bool(book.genres))
        ]

        status_line = "   Fields: "
        for field_name, is_populated in status_fields:
            if is_populated:
                status_line += f"[green]✓[/green] {field_name}  "
            else:
                status_line += f"[red]✗[/red] {field_name}  "

        console.print(status_line)

    console.print("\n" + "=" * 80)
    console.print("\n[dim]Controls: [number] to view details, [q]uit, [s]ave JSON, [m]arc export[/dim]")

    # Interactive menu
    while True:
        try:
            choice = console.input("\n[bold]Enter choice: [/bold]").lower().strip()

            if choice == 'q':
                break
            elif choice == 's':
                # Save results to JSON file
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"manga_results_{timestamp}.json"

                results_data = [
                    {
                        "series_name": book.series_name,
                        "volume_number": book.volume_number,
                        "book_title": book.book_title,
                        "authors": book.authors,
                        "msrp_cost": book.msrp_cost,
                        "isbn_13": book.isbn_13,
                        "publisher_name": book.publisher_name,
                        "copyright_year": book.copyright_year,
                        "description": book.description,
                        "physical_description": book.physical_description,
                        "genres": book.genres,
                        "warnings": book.warnings,
                        "barcode": book.barcode
                    }
                    for book in books
                ]

                with open(filename, 'w') as f:
                    json.dump(results_data, f, indent=2)

                console.print(f"[green]✓ Results saved to {filename}[/green]")
            elif choice == 'm':
                # Export to MARC format
                try:
                    from marc_exporter import export_books_to_marc
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    filename = f"manga_marc_{timestamp}.mrc"

                    export_books_to_marc(books, filename, "M")
                    console.print(f"[green]✓ MARC records exported to {filename}[/green]")
                    console.print(f"[dim]Contains {len(books)} bibliographic records with holding information[/dim]")
                except ImportError:
                    console.print("[red]Error: pymarc library not installed. Install with: pip install pymarc[/red]")
                except Exception as e:
                    console.print(f"[red]Error exporting MARC records: {e}[/red]")
            elif choice.isdigit():
                book_index = int(choice) - 1
                if 0 <= book_index < len(books):
                    show_book_details(books[book_index], console)
                    console.print("\n[dim]Press Enter to return to list...[/dim]")
                    console.input()
                    # Redisplay the list
                    display_text_list(books, console)
                    break
                else:
                    console.print("[yellow]Invalid book number. Please select a valid number.[/yellow]")
            else:
                console.print("[yellow]Invalid choice. Use number to view details, 'q' to quit, 's' to save JSON, or 'm' for MARC export.[/yellow]")

        except KeyboardInterrupt:
            console.print("\n[yellow]Exiting list view...[/yellow]")
            break

def show_book_details(book: BookInfo, console: Console):
    """Show detailed information for a single book"""

    console.print("\n" + "=" * 60)
    console.print(f"[bold blue]Book Details - Volume {book.volume_number}[/bold blue]")
    console.print("=" * 60)

    formatted_authors = DataValidator.format_authors_list(book.authors)

    details = [
        ("Title", book.book_title),
        ("Series", book.series_name),
        ("Authors", formatted_authors),
        ("Volume", str(book.volume_number)),
        ("Barcode", book.barcode or "Not assigned"),
        ("MSRP", f"${book.msrp_cost:.2f}" if book.msrp_cost else "Unknown"),
        ("ISBN-13", book.isbn_13 or "Unknown"),
        ("Publisher", book.publisher_name or "Unknown"),
        ("Copyright Year", str(book.copyright_year) if book.copyright_year else "Unknown"),
        ("Description", book.description or "No description available"),
        ("Physical Description", book.physical_description or "No physical description available"),
        ("Genres", ", ".join(book.genres) if book.genres else "No genres listed")
    ]

    for field_name, value in details:
        console.print(f"\n[bold]{field_name}:[/bold]")
        # Wrap long text for better readability
        if len(value) > 80:
            # Simple text wrapping
            words = value.split()
            lines = []
            current_line = []
            for word in words:
                if len(' '.join(current_line + [word])) <= 80:
                    current_line.append(word)
                else:
                    lines.append(' '.join(current_line))
                    current_line = [word]
            if current_line:
                lines.append(' '.join(current_line))

            for line in lines:
                console.print(f"  {line}")
        else:
            console.print(f"  {value}")

    # Show warnings if any
    if book.warnings:
        console.print(f"\n[bold yellow]Warnings:[/bold yellow]")
        for warning in book.warnings:
            console.print(f"  ⚠️  {warning}")

    console.print("\n" + "=" * 60)

def main():
    """Main function to run the manga lookup tool with multiple series support"""
    console = Console()
    project_state = ProjectState()

    rprint("[bold blue]Manga Lookup Tool[/bold blue]")
    rprint("[dim]Enhanced version with multiple series, volume ranges, and barcode assignment[/dim]")

    try:
        # Initialize APIs
        deepseek_api = DeepSeekAPI()

        # Get starting barcode
        rprint("\n[bold]Barcode Configuration[/bold]")
        rprint("[dim]Enter starting barcode (e.g., 'T000001' or 'MANGA001'):[/dim]")
        start_barcode = Prompt.ask("[bold]Starting barcode[/bold]", default="T000001")

        # Collect multiple series with volume ranges
        series_entries = []
        rprint("\n[bold]Series Entry[/bold]")
        rprint("[dim]Enter manga series names with volume ranges (e.g., '1-5,7,10').[/dim]")
        rprint("[dim]Leave series name blank when done.[/dim]")

        while True:
            series_name = Prompt.ask("\n[bold]Enter manga series name[/bold]", default="")
            if not series_name:
                break

            volume_input = Prompt.ask("[bold]Enter volume numbers/ranges[/bold] (e.g., '1-5,7,10')")

            try:
                volumes = parse_volume_range(volume_input)
                series_entries.append({
                    'original_name': series_name,
                    'volumes': volumes
                })
                rprint(f"[green]✓ Added {series_name} with volumes: {', '.join(map(str, volumes))}[/green]")
            except ValueError as e:
                rprint(f"[red]Error parsing volume range: {e}[/red]")

        if not series_entries:
            rprint("\n[yellow]No series entered. Exiting.[/yellow]")
            return

        # Confirm all series names before starting lookups
        rprint("\n[bold]Series Confirmation[/bold]")
        rprint("[dim]Confirming series names before starting lookups...[/dim]")

        confirmed_series_entries = []
        for series_entry in series_entries:
            series_name = series_entry['original_name']
            volumes = series_entry['volumes']

            # Correct series name using DeepSeek API
            rprint(f"\n[cyan]Correcting series name: {series_name}[/cyan]")
            suggestions = deepseek_api.correct_series_name(series_name)

            if len(suggestions) > 1:
                rprint("\n[bold]Please select the correct series name:[/bold]")
                for i, suggestion in enumerate(suggestions, 1):
                    # Get additional info for each suggestion
                    series_info = deepseek_api._get_series_info(suggestion)
                    if series_info:
                        rprint(f"{i}. {suggestion} - {series_info}")
                    else:
                        rprint(f"{i}. {suggestion}")

                rprint(f"\n{len(suggestions) + 1}. [yellow]Look Again[/yellow] - Search for more options")
                rprint(f"{len(suggestions) + 2}. [red]Skip[/red] - Skip this series")

                choice = IntPrompt.ask("\nSelect option", choices=[str(i) for i in range(1, len(suggestions) + 3)])

                if choice <= len(suggestions):
                    selected_series = suggestions[choice - 1]
                    rprint(f"[green]Using series: {selected_series}[/green]")
                elif choice == len(suggestions) + 1:
                    # Look Again - make another API call
                    rprint("[cyan]Searching for more options...[/cyan]")
                    suggestions = deepseek_api.correct_series_name(series_name)
                    continue  # Restart the selection process with new suggestions
                else:
                    # Skip this series
                    rprint("[yellow]Skipping this series[/yellow]")
                    selected_series = None
                    break
            else:
                selected_series = suggestions[0]
                rprint(f"[green]Using series: {selected_series}[/green]")

            # Add to confirmed entries only if not skipped
            if selected_series:
                confirmed_series_entries.append({
                    'original_name': series_name,
                    'confirmed_name': selected_series,
                    'volumes': volumes
                })
            else:
                rprint(f"[yellow]Skipped {series_name} with volumes: {', '.join(map(str, volumes))}[/yellow]")

        rprint("\n[green]✓ All series names confirmed![/green]")

        # Process each series
        all_books = []
        total_volumes = sum(len(entry['volumes']) for entry in confirmed_series_entries)

        rprint(f"\n[bold]Processing {len(confirmed_series_entries)} series with {total_volumes} total volumes...[/bold]")

        for series_entry in confirmed_series_entries:
            series_name = series_entry['confirmed_name']
            volumes = series_entry['volumes']

            # Fetch book data for each volume
            rprint(f"\n[cyan]Processing {series_name} - {len(volumes)} volumes...[/cyan]")

            series_books = []
            for i, volume in enumerate(volumes, 1):
                rprint(f"[dim]Processing volume {volume} ({i}/{len(volumes)})...[/dim]")

                book_data = deepseek_api.get_book_info(series_name, volume, project_state)
                if book_data:
                    book = process_book_data(book_data, volume)
                    series_books.append(book)

                    # Show warnings if any
                    if book.warnings:
                        for warning in book.warnings:
                            rprint(f"[yellow]Warning for volume {volume}: {warning}[/yellow]")

                    rprint(f"[green]✓ Found volume {volume}[/green]")
                else:
                    rprint(f"[yellow]✗ Volume {volume} not found[/yellow]")

            all_books.extend(series_books)

        if not all_books:
            rprint("\n[red]No books found for the specified series and volume ranges.[/red]")
            return

        # Assign barcodes
        rprint(f"\n[cyan]Assigning barcodes starting from {start_barcode}...[/cyan]")
        barcodes = generate_sequential_barcodes(start_barcode, len(all_books))
        for book, barcode in zip(all_books, barcodes):
            book.barcode = barcode

        # Display results with barcodes
        rprint("\n[bold]Results Summary:[/bold]")
        for book in all_books:
            formatted_authors = DataValidator.format_authors_list(book.authors)
            rprint(f"  Volume {book.volume_number}: {book.book_title}")
            rprint(f"    Authors: {formatted_authors}")
            rprint(f"    Publisher: {book.publisher_name or 'Unknown'}")
            rprint(f"    MSRP: ${book.msrp_cost:.2f}" if book.msrp_cost else "    MSRP: Unknown")
            rprint(f"    Barcode: {book.barcode}")

        # Display enhanced text-based list with barcodes
        display_text_list(all_books, console)

        # Record interaction
        series_info = ", ".join([f"{entry['confirmed_name']} ({len(entry['volumes'])} vols)" for entry in confirmed_series_entries])
        project_state.record_interaction(f"Multiple series: {series_info}", len(all_books))

        rprint(f"\n[green]Found {len(all_books)} books. Project state updated.[/green]")

    except KeyboardInterrupt:
        rprint("\n[yellow]Operation cancelled by user.[/yellow]")
    except Exception as e:
        rprint(f"\n[red]An error occurred: {e}[/red]")

if __name__ == "__main__":
    main()
