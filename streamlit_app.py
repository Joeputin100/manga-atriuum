# Manga Lookup Tool - Dev Version
# Trivial change to trigger redeploy
# Trivial change to trigger redeploy
# Updated for deployment
"""
Manga Lookup Tool - Streamlit Web App

A web interface for the manga lookup tool with progress tracking,
real-time updates, and streamlined UI.

NOTE: This app is designed to run on Streamlit Cloud only.
Local execution requires Streamlit installation.
"""

# Check if Streamlit is available - if not, provide helpful error message
import sys

try:
    import streamlit as st
except ImportError:
    sys.exit(1)

import contextlib
import html
import json
import tempfile
import time
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

# from label_generator import generate_pdf_sheet

# Import cover fetchers
from mal_cover_fetcher import MALCoverFetcher

# Import existing core logic
from manga_lookup import (
    BookInfo,
    DeepSeekAPI,
    GoogleBooksAPI,
    ProjectState,
    generate_sequential_barcodes,
    parse_volume_range,
    process_book_data,
)
from mangadex_cover_fetcher import MangaDexCoverFetcher

# Import MARC exporter
from marc_exporter import export_books_to_marc

SECONDS_IN_MINUTE = 60
SECONDS_IN_HOUR = 3600
EXPECTED_SERIES_COUNT = 2
EXPECTED_SERIES_COUNT_2 = 3
MAX_DESCRIPTION_LENGTH = 150
MAX_SHORT_DESCRIPTION_LENGTH = 100


def initialize_session_state():
    """Initialize session state variables"""
    if "series_entries" not in st.session_state:
        st.session_state.series_entries = []
    if "confirmed_series" not in st.session_state:
        st.session_state.confirmed_series = []
    if "all_books" not in st.session_state:
        st.session_state.all_books = []
    if "processing_state" not in st.session_state:
        st.session_state.processing_state = {
            "is_processing": False,
            "current_series": None,
            "current_volume": None,
            "progress": 0,
            "total_volumes": 0,
            "start_time": None,
        }
    if "project_state" not in st.session_state:
        st.session_state.project_state = ProjectState()
    if "pending_series_name" not in st.session_state:
        st.session_state.pending_series_name = None
    if "selected_series" not in st.session_state:
        st.session_state.selected_series = None
    if "original_series_name" not in st.session_state:
        st.session_state.original_series_name = None
    if "start_barcode" not in st.session_state:
        st.session_state.start_barcode = "T000001"
    # Reset processing state if stuck
    if (
        st.session_state.processing_state.get("is_processing", False)
        and not st.session_state.all_books
    ):
        st.session_state.processing_state["is_processing"] = False


def get_volume_1_isbn(series_name: str) -> str | None:
    """Get ISBN for volume 1 of a series using DeepSeek API"""
    try:
        deepseek_api = DeepSeekAPI()
        book_data = deepseek_api.get_book_info(
            series_name,
            1,
            st.session_state.project_state,
        )
        if book_data and book_data.get("isbn_13"):
            return book_data["isbn_13"]
        else:
            return None
    except OSError:
        return None


def fetch_cover_for_book(book: BookInfo) -> str | None:
    """Fetch cover image URL, prioritizing English editions"""

    # Try Google Books first for English covers
    try:
        google_api = GoogleBooksAPI()
        cover_url = google_api.get_series_cover_image(
            book.series_name,
            book.volume_number,
            (
                st.session_state.project_state
                if "project_state" in st.session_state
                else None
            ),
        )
        if cover_url:
            return cover_url
    except OSError:
        pass

    # Fallback to MAL
    with contextlib.suppress(OSError):
        MALCoverFetcher()

    # Fallback to MangaDex
    try:
        mangadex_fetcher = MangaDexCoverFetcher()
        cover_url = mangadex_fetcher.fetch_cover(book.series_name, book.volume_number)
        if cover_url:
            return cover_url
    except OSError:
        pass

    return None


def process_single_volume(series_name, volume, project_state):
    """Process a single volume and return book info"""
    try:
        deepseek_api = DeepSeekAPI()
        google_books_api = GoogleBooksAPI()
        book_data = deepseek_api.get_book_info(series_name, volume, project_state)
        if book_data:
            book = process_book_data(book_data, volume, google_books_api, project_state)
            return book, None
        else:
            return None, f"Volume {volume} not found"
    except OSError as e:
        return None, f"Error processing volume {volume}: {e!s}"


def process_series():
    """Process all confirmed series with threaded execution for better progress updates"""
    # Create a list of all volumes to process
    all_volumes = [
        (series_entry["confirmed_name"], volume)
        for series_entry in st.session_state.series_entries
        for volume in series_entry["volumes"]
    ]

    if not all_volumes:
        st.session_state.processing_state["is_processing"] = False
        st.warning("No volumes to process. Please add volumes to your series first.")
        return

    # Initialize API (not used directly in this function but needed for imports)
    try:
        _ = DeepSeekAPI()  # Create instance to verify API is available
    except ValueError:
        st.error("API configuration error. Please check your environment variables.")
        st.session_state.processing_state["is_processing"] = False
        return

    all_books = []
    errors = []

    # Show initial processing message
    st.info("🔄 Please wait while we look up your manga volumes...")

    # Process volumes with threading
    with ThreadPoolExecutor(max_workers=15) as executor:
        # Submit all tasks
        future_to_volume = {
            executor.submit(
                process_single_volume,
                series_name,
                volume,
                st.session_state.project_state,
            ): (series_name, volume)
            for series_name, volume in all_volumes
        }

        # Process results as they complete
        for i, future in enumerate(as_completed(future_to_volume)):
            series_name, volume = future_to_volume[future]

            # Update progress
            st.session_state.processing_state["current_series"] = series_name
            st.session_state.processing_state["current_volume"] = volume
            st.session_state.processing_state["progress"] = i + 1

            book, error = future.result()
            if book:
                all_books.append(book)
            elif error:
                errors.append(error)

    # Assign barcodes
    start_barcode = st.session_state.get("start_barcode", "T000001")
    barcodes = generate_sequential_barcodes(start_barcode, len(all_books))
    for book, barcode in zip(all_books, barcodes, strict=False):
        book.barcode = barcode

    st.session_state.all_books = all_books
    st.session_state.processing_state["is_processing"] = False

    # Record interaction
    series_info = ", ".join(
        [
            f"{entry['confirmed_name']} ({len(entry['volumes'])} vols)"
            for entry in st.session_state.series_entries
        ],
    )
    st.session_state.project_state.record_interaction(
        f"Multiple series: {series_info}",
        len(all_books),
    )

    # Show results
    if all_books:
        st.success(f"✓ Found {len(all_books)} books!")
    if errors:
        st.warning(f"⚠️ {len(errors)} volumes had issues:")
        for error in errors:
            st.write(f"• {error}")


def display_duck_animation():

    st.image("https://media.giphy.com/media/WzA4Vj6V8UOEX10jMj/giphy.gif")


def calculate_elapsed_time(start_time):
    """Calculate elapsed time"""
    if not start_time:
        return "0 seconds"

    elapsed = time.time() - start_time
    if elapsed < SECONDS_IN_MINUTE:
        return f"{int(elapsed)} seconds"
    if elapsed < SECONDS_IN_HOUR:
        minutes = int(elapsed / SECONDS_IN_MINUTE)
        seconds = int(elapsed % SECONDS_IN_MINUTE)
        return f"{minutes}m {seconds}s"
    hours = int(elapsed / SECONDS_IN_HOUR)
    minutes = int((elapsed % SECONDS_IN_HOUR) / SECONDS_IN_MINUTE)
    return f"{hours}h {minutes}m"


def calculate_eta(start_time, progress, total):
    """Calculate estimated time remaining"""
    if progress == 0:
        return "Calculating..."

    elapsed = time.time() - start_time
    if elapsed == 0:
        return "Calculating..."

    rate = progress / elapsed
    remaining = total - progress
    if rate > 0:
        eta_seconds = remaining / rate
        if eta_seconds < SECONDS_IN_MINUTE:
            return f"{int(eta_seconds)} seconds"
        if eta_seconds < SECONDS_IN_HOUR:
            return f"{int(eta_seconds/SECONDS_IN_MINUTE)} minutes"
        return f"{int(eta_seconds/SECONDS_IN_HOUR)} hours"
    return "Calculating..."


def display_progress_section():
    """Display progress tracking"""
    state = st.session_state.processing_state
    progress = state["progress"]
    total = state["total_volumes"]

    if progress == 0:
        st.write("Preparing to lookup manga volumes...")
    else:
        st.write(f"Processing {progress} of {total} volumes")
        if state["current_series"]:
            st.info(
                f"Current: {state['current_series']} - Volume {state['current_volume']}",
            )

    display_duck_animation()
    st.caption("Please wait...")


def series_input_form():
    if "barcode_confirmed" not in st.session_state:
            st.session_state.barcode_confirmed = False
    if st.button("Reset Barcode State"):
        if "barcode_confirmed" in st.session_state:
            del st.session_state.barcode_confirmed
        if "start_barcode" in st.session_state:
            del st.session_state.start_barcode
        if "start_barcode_input" in st.session_state:
            del st.session_state.start_barcode_input
        st.rerun()
    """Multi-series input form"""
    st.header("📚 Manga Series Input")
    if True:
        # Starting barcode - show until used
        # Starting barcode - always show with current value
        if not st.session_state.get("barcode_confirmed", False):
            st.markdown(
                "<i style='color: gray;'>(e.g. T000001)</i>",
                unsafe_allow_html=True,
            )
            start_barcode_input = st.text_input(
                "Starting Barcode",
                placeholder="Enter starting barcode",
                help="Enter starting barcode (e.g., T000001 or MANGA001)",
                key="start_barcode_input",
            )
