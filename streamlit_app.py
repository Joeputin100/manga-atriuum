#!/usr/bin/env python3
# Updated for deployment
"""
Manga Lookup Tool - Streamlit Web App

A web interface for the manga lookup tool with progress tracking,
real-time updates, and streamlined UI.

NOTE: This app is designed to run on Streamlit Cloud only.
Local execution requires Streamlit installation.
"""

# Check if Streamlit is available - if not, provide helpful error message
try:
    import streamlit as st
except ImportError:
    print("ERROR: Streamlit is not installed.")
    print("This app is designed to run on Streamlit Cloud.")
    print("For local development, install Streamlit with: pip install streamlit")
    print("Or deploy directly to Streamlit Cloud.")
    exit(1)

import os
import json
import time
import pandas as pd
from datetime import datetime
from typing import Optional
from concurrent.futures import ThreadPoolExecutor, as_completed

# Import existing core logic
from manga_lookup import (
    BookInfo, DeepSeekAPI, DataValidator, ProjectState, GoogleBooksAPI,
    parse_volume_range, generate_sequential_barcodes, process_book_data
)

# Import MARC exporter
from marc_exporter import export_books_to_marc
# Import cover fetchers

from google_books_client import GoogleBooksClient

from mal_cover_fetcher import MALCoverFetcher

from mangadex_cover_fetcher import MangaDexCoverFetcher


def initialize_session_state():
    """Initialize session state variables"""
    if 'series_entries' not in st.session_state:
        st.session_state.series_entries = []
    if 'confirmed_series' not in st.session_state:
        st.session_state.confirmed_series = []
    if 'all_books' not in st.session_state:
        st.session_state.all_books = []
    if 'processing_state' not in st.session_state:
        st.session_state.processing_state = {
            'is_processing': False,
            'current_series': None,
            'current_volume': None,
            'progress': 0,
            'total_volumes': 0,
            'start_time': None
    }
    if 'project_state' not in st.session_state:
        st.session_state.project_state = ProjectState()
    if 'pending_series_name' not in st.session_state:
        st.session_state.pending_series_name = None
    if 'selected_series' not in st.session_state:
        st.session_state.selected_series = None
    if 'original_series_name' not in st.session_state:
        st.session_state.original_series_name = None
    if 'start_barcode' not in st.session_state:
        st.session_state.start_barcode = "T000001"
def get_volume_1_isbn(series_name: str) -> Optional[str]:
    """Get ISBN for volume 1 of a series using DeepSeek API"""
    try:
        deepseek_api = DeepSeekAPI()
        book_data = deepseek_api.get_book_info(series_name, 1, st.session_state.project_state)
        if book_data and book_data.get('isbn_13'):
            return book_data['isbn_13']
        return None
    except Exception:
        return None


def fetch_cover_for_book(book: BookInfo) -> Optional[str]:
    """Fetch cover image for a book using available cover fetchers"""
    
    # Try MAL first
    mal_fetcher = MALCoverFetcher()
    cover_url = mal_fetcher.fetch_cover_for_series(book.series_name)
    if cover_url:
        return cover_url
    
    # Try MangaDex as fallback
    mangadex_fetcher = MangaDexCoverFetcher()
    cover_url = mangadex_fetcher.fetch_cover_for_series(book.series_name)
    if cover_url:
        return cover_url
    
    # Try Google Books as last resort
    google_client = GoogleBooksClient()
    cover_url = google_client.get_cover_image(book.series_name, 1)
    return cover_url


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
    except Exception as e:
        return None, f"Error processing volume {volume}: {str(e)}"



def main():
    """Main application logic"""
    st.title("📚 Manga Lookup Tool")

    # Initialize session state
    initialize_session_state()

    # Handle pending series confirmation
    if st.session_state.pending_series_name:
        confirm_single_series(st.session_state.pending_series_name)
        return

    # Check if processing
    if st.session_state.processing_state["is_processing"]:
        st.header("🔄 Processing Series")

        # Display progress
        display_progress_section()

        # Processing logic
        process_series()

    elif st.session_state.all_books:
        # Display results
        st.header("📚 Lookup Results")

        # Create a dataframe for display
        import pandas as pd
        books_data = []
        for book in st.session_state.all_books:
            books_data.append({
                'Barcode': book.barcode,
                'Series': book.series_name,
                'Volume': book.volume_number,
                'Title': book.book_title or 'N/A',
                'ISBN': book.isbn_13 or 'N/A',
                'Authors': ', '.join(book.authors) if book.authors else 'N/A',
                'Publisher': book.publisher_name or 'N/A',
                'MSRP': f"${book.msrp_cost:.2f}" if book.msrp_cost else 'N/A'
            })

        df = pd.DataFrame(books_data)
        st.dataframe(df, use_container_width=True)

        # Export options
        st.subheader("Export Options")
        if st.button("Export to MARC", type="primary"):
            try:
                marc_data = export_books_to_marc(st.session_state.all_books)
                st.download_button(
                    label="Download MARC file",
                    data=marc_data,
                    file_name="manga_collection.mrc",
                    mime="application/octet-stream"
                )
            except Exception as e:
                st.error(f"Export failed: {e}")

        # Clear results and start over
        if st.button("Start New Lookup"):
            st.session_state.all_books = []
            st.session_state.series_entries = []
            st.session_state.confirmed_series = []
            st.rerun()

    else:
        # Show series input form
        series_input_form()


if __name__ == "__main__":
    main()
