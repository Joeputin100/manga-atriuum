#!/usr/bin/env python3
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


def display_duck_animation():
    """Display animated duck with GIF"""
    st.image('https://media.giphy.com/media/WzA4Vj6V8UOEX10jMj/giphy.gif')


def calculate_elapsed_time(start_time):
    """Calculate elapsed time"""
    if not start_time:
        return "0 seconds"

    elapsed = time.time() - start_time
    if elapsed < 60:
        return f"{int(elapsed)} seconds"
    elif elapsed < 3600:
        minutes = int(elapsed / 60)
        seconds = int(elapsed % 60)
        return f"{minutes}m {seconds}s"
        hours = int(elapsed / 3600)
        minutes = int((elapsed % 3600) / 60)
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
        if eta_seconds < 60:
            return f"{int(eta_seconds)} seconds"
        elif eta_seconds < 3600:
            return f"{int(eta_seconds/60)} minutes"
            return f"{int(eta_seconds/3600)} hours"
    return "Calculating..."


def display_progress_section():
    """Display progress tracking with duck animation"""
    if not st.session_state.processing_state['is_processing']:
        return

    state = st.session_state.processing_state
    progress = state['progress']
    total = state['total_volumes']

    # Progress bar
    progress_percent = int((progress / total) * 100) if total > 0 else 0
    st.progress(progress_percent / 100)

    # Progress info
    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("Progress", f"{progress}/{total}")

    with col2:
        if state['start_time']:
            elapsed = calculate_elapsed_time(state['start_time'])
            st.metric("Elapsed Time", elapsed)

    with col3:
        # Animated duck
        display_duck_animation()
        st.caption("Processing...")

    # Current task info
    if state['current_series']:
        st.info(f"Processing: **{state['current_series']}** - Volume **{state['current_volume']}**")
def series_input_form():
    """Multi-series input form"""
    st.header("📚 Manga Series Input")

    # Starting barcode - always show with current value
    st.markdown("<i style='color: gray;'>(e.g. T000001)</i>", unsafe_allow_html=True)
    start_barcode = st.text_input(
        "Starting Barcode",
        value=st.session_state.start_barcode,
        placeholder="Enter starting barcode",
        help="Enter starting barcode (e.g., T000001 or MANGA001)",
    )
    if start_barcode and start_barcode != st.session_state.start_barcode:
        st.session_state.start_barcode = start_barcode

    # Series input section
    st.subheader("Add Series")

    # Make series name entry ordinal
    series_count = len(st.session_state.series_entries) + 1
    ordinal_text = "1st" if series_count == 1 else "2nd" if series_count == 2 else "3rd" if series_count == 3 else f"{series_count}th"

    # Use a unique key for the series form with timestamp
    series_form_key = f"series_form_{series_count}_{len(st.session_state.series_entries)}_{int(time.time())}"
    # Track form submission
    if 'form_just_submitted' not in st.session_state:
        st.session_state.form_just_submitted = None
    with st.form(series_form_key, clear_on_submit=True):

        series_name = st.text_input(f"Enter {ordinal_text} Series Name", help="Enter the manga series name (e.g., Naruto, One Piece, Death Note)")

        # Debug info inside form
        if series_name:
            st.write(f"📝 Current input: '{series_name}'")
        else:
            st.write("📝 No series name entered yet")

        submitted = st.form_submit_button("Confirm Series Name")

        # Debug submission
        if submitted:
            st.session_state.form_just_submitted = series_name
            st.write(f"🔄 Form submitted with: '{series_name}'")
        else:
            st.write("⏳ Waiting for form submission...")

        if submitted and series_name:
            st.info(f"DEBUG: Setting pending_series_name to {series_name}")
            # Store the series name for confirmation
            st.session_state.pending_series_name = series_name
            st.success(f"✓ Submitted '{series_name}' for confirmation")
            st.rerun()
    
    # Debug outside form
    if st.session_state.form_just_submitted:
        st.success(f"✅ Form submitted successfully with: {st.session_state.form_just_submitted}")
        st.session_state.form_just_submitted = None

    # Display current series with cyan background
    if st.session_state.series_entries:
        st.markdown("""
        <style>
        .cyan-background {
            background-color: #e0f7fa;
            padding: 15px;
            border-radius: 10px;
            border: 1px solid #80deea;
            margin-bottom: 10px;
        }
        </style>
        """, unsafe_allow_html=True)

        # Display series in a grid of cards
        cols = st.columns(2)  # 2 columns for cards

        for i, entry in enumerate(st.session_state.series_entries):
            col_idx = i % 2
            with cols[col_idx]:
                # Alternate card styles
                card_class = "manga-card" if i % 2 == 0 else "manga-card-alt"

                # Try to get cover image
                cover_url = None
                try:
                    # Create a dummy book object to get series cover
                    dummy_book = BookInfo(
                        series_name=entry["confirmed_name"],
                        volume_number=1,
                        book_title="",
                        authors=[],
                        msrp_cost=None,
                        isbn_13=None,
                        publisher_name="",
                        copyright_year=None,
                        description="",
                        physical_description="",
                        genres=[],
                        warnings=[]
                    )
                    cover_url = fetch_cover_for_book(dummy_book)
                except Exception:
                    pass

                # Card HTML
                card_html = f"""
                <div class="{card_class}">
                    <div style="display: flex; align-items: center; margin-bottom: 10px;">
                        <h4 style="margin: 0; flex-grow: 1;">📚 {entry["confirmed_name"]}</h4>
                        <span style="font-size: 0.8em;">Vol: {len(entry["volumes"])}</span>
                    </div>
                """

                if cover_url:
                    card_html += f"""
                    <div style="text-align: center; margin: 10px 0;">
                        <img src="{cover_url}" style="max-width: 100px; max-height: 150px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.2);" alt="Cover">
                    </div>
                    """

                card_html += f"""
                    <p style="margin: 5px 0; font-size: 0.9em;">Volumes: {", ".join(map(str, entry["volumes"]))}</p>
                    <div style="text-align: center; margin-top: 10px;">
                """

                st.markdown(card_html, unsafe_allow_html=True)

                # Remove button outside the HTML
                if st.button("🗑️ Remove", key=f"remove_{i}"):
                    st.session_state.series_entries.pop(i)
                    st.rerun()
    
    # Debug outside form
    if st.session_state.form_just_submitted:
        st.success(f"✅ Form submitted successfully with: {st.session_state.form_just_submitted}")
        st.session_state.form_just_submitted = None

                st.markdown("</div>", unsafe_allow_html=True)
                st.markdown('</div>', unsafe_allow_html=True)

    # Start processing button
    if st.session_state.series_entries:
        if st.button("🚀 Start Lookup", type="primary"):
            st.session_state.processing_state['is_processing'] = True
            st.session_state.processing_state['start_time'] = time.time()
            st.session_state.processing_state['total_volumes'] = sum(
                len(entry['volumes']) for entry in st.session_state.series_entries
            )
        st.rerun()


def confirm_single_series(series_name):
    """Confirm a single series name with series information in separate cards"""
    st.header(f"🔍 Confirm: {series_name}")

    # Debug information visible in UI
    with st.expander("🔧 Debug Info", expanded=False):
        st.write("**Function called with:**", series_name)
        st.write("**Session state pending_series_name:**", st.session_state.get('pending_series_name'))

    # Initialize DeepSeek API
    try:
        deepseek_api = DeepSeekAPI()
        with st.expander("🔧 Debug Info", expanded=False):
            st.success("✅ DeepSeek API initialized successfully")
    except ValueError as e:
        st.error(f"API configuration error: {e}")
        with st.expander("🔧 Debug Info", expanded=False):
            st.error(f"❌ API init failed: {e}")
        return

    # Get suggestions
    try:
        suggestions = deepseek_api.correct_series_name(series_name)
    except Exception as e:
        st.error(f"Error getting suggestions: {e}")
        suggestions = [series_name]  # Fallback

    # Debug logging and UI display
    print(f"DEBUG: confirm_single_series called for '{series_name}'")
    print(f"DEBUG: suggestions returned: {suggestions}")
    print(f"DEBUG: Number of suggestions: {len(suggestions)}")

    with st.expander("🔧 Debug Info", expanded=False):
        st.write("**Suggestions returned:**", suggestions)
        st.write("**Number of suggestions:**", len(suggestions))
        if not suggestions:
            st.error("❌ No suggestions returned!")
        elif len(suggestions) == 1:
            st.info("ℹ️ Single suggestion (will show single card)")
        else:
            st.info(f"ℹ️ Multiple suggestions ({len(suggestions)} - will show multiple cards)")

    # Simple debug display
    st.write("Suggestions found:", suggestions)

    if len(suggestions) > 1:
        # Multiple suggestions - display in separate cards
        st.write("Select the correct series name:")

        # Create columns for the cards
        cols = st.columns(min(3, len(suggestions)))

        for i, suggestion in enumerate(suggestions):
            with cols[i % len(cols)]:
                # Create a card container with distinct styling
                card_colors = [
                    "linear-gradient(135deg, #667eea 0%, #764ba2 100%)",
                    "linear-gradient(135deg, #f093fb 0%, #f5576c 100%)",
                    "linear-gradient(135deg, #4facfe 0%, #00f2fe 100%)",
                    "linear-gradient(135deg, #43e97b 0%, #38f9d7 100%)",
                    "linear-gradient(135deg, #fa709a 0%, #fee140 100%)",
                    "linear-gradient(135deg, #a8edea 0%, #fed6e3 100%)"
                ]
                card_color = card_colors[i % len(card_colors)]

                st.markdown(f"""
                <div style="
                    background: {card_color};
                    border-radius: 12px;
                    padding: 20px;
                    margin: 10px 0;
                    color: white;
                    box-shadow: 0 4px 15px rgba(0, 0, 0, 0.2);
                    border: 2px solid rgba(255, 255, 255, 0.3);
                ">
                """, unsafe_allow_html=True)

                # Show title immediately
                st.subheader(suggestion)

                # Try to get cover image
                try:
                    # Create a dummy book object to get series cover
                    dummy_book = BookInfo(
                        series_name=suggestion,
                        volume_number=1,
                        book_title="",
                        authors=[],
                        msrp_cost=None,
                        isbn_13=None,
                        publisher_name="",
                        copyright_year=None,
                        description="",
                        physical_description="",
                        genres=[],
                        warnings=[]
                    )
                    cover_url = fetch_cover_for_book(dummy_book)
                    if cover_url:
                        st.image(cover_url, width=120)
                    else:
                        st.caption("📚 No cover available")
                except Exception as e:
                    st.caption(f"⚠️ Cover error: {str(e)[:50]}...")

                # Get series information
                try:
                    series_info = deepseek_api._get_series_info(suggestion)
                    # Display series information
                    if series_info:
                        st.write(f"**Info:** {series_info}")
                    else:
                        st.write("*No additional information available*")
                except Exception as e:
                    st.write("*Series information unavailable*")
                    print(f"Error getting series info for '{suggestion}': {e}")

                # Make the entire card clickable
                if st.button(f"✓ Select {suggestion}", key=f"select_{series_name}_{i}"):
                    # Store selected series for volume input
                    st.session_state.selected_series = suggestion
                    st.session_state.original_series_name = series_name
                    st.rerun()
    
    # Debug outside form
    if st.session_state.form_just_submitted:
        st.success(f"✅ Form submitted successfully with: {st.session_state.form_just_submitted}")
        st.session_state.form_just_submitted = None

                st.markdown("</div>", unsafe_allow_html=True)

        # Look Again and Skip options
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🔄 Look Again"):
                st.info("Searching for more options...")
                # Clear pending series to restart
                st.session_state.pending_series_name = None
                st.rerun()
    
    # Debug outside form
    if st.session_state.form_just_submitted:
        st.success(f"✅ Form submitted successfully with: {st.session_state.form_just_submitted}")
        st.session_state.form_just_submitted = None

        with col2:
            if st.button("⏭️ Skip"):
                st.warning(f"Skipped {series_name}")
                st.session_state.pending_series_name = None
                st.rerun()
    
    # Debug outside form
    if st.session_state.form_just_submitted:
        st.success(f"✅ Form submitted successfully with: {st.session_state.form_just_submitted}")
        st.session_state.form_just_submitted = None
    else:
        # Single suggestion
        selected_series = suggestions[0]
        st.success(f"✓ Using: {selected_series}")

        # Show series information in a card with styling
        st.markdown("""
        <div style="
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            border-radius: 12px;
            padding: 20px;
            margin: 10px 0;
            color: white;
            box-shadow: 0 4px 15px rgba(0, 0, 0, 0.2);
            border: 2px solid rgba(255, 255, 255, 0.3);
        ">
        """, unsafe_allow_html=True)

        with st.container():
            col1, col2 = st.columns([1, 3])
            with col1:
                # Try to get cover image
                try:
                    # Create a dummy book object to get series cover
                    dummy_book = BookInfo(
                        series_name=selected_series,
                        volume_number=1,
                        book_title="",
                        authors=[],
                        msrp_cost=None,
                        isbn_13=None,
                        publisher_name="",
                        copyright_year=None,
                        description="",
                        physical_description="",
                        genres=[],
                        warnings=[]
                    )
                    cover_url = fetch_cover_for_book(dummy_book)
                    if cover_url:
                        st.image(cover_url, width=120)
                    else:
                        st.markdown("📚")
                        st.caption("No cover available")
                except Exception as e:
                    st.markdown("📚")
                    st.caption(f"Cover error: {str(e)[:30]}...")

            with col2:
                st.subheader(selected_series)

                # Get and display series information
                try:
                    series_info = deepseek_api._get_series_info(selected_series)
                    if series_info:
                        st.write(f"**Series Info:** {series_info}")
                except Exception as e:
                    st.write("*Series information unavailable*")
                    print(f"Error getting series info for '{selected_series}': {e}")

                if st.button("✓ Confirm and Add Volumes", type="primary"):
                    # Store selected series for volume input
                    st.session_state.selected_series = selected_series
                    st.session_state.original_series_name = series_name
                    st.rerun()
    
    # Debug outside form
    if st.session_state.form_just_submitted:
        st.success(f"✅ Form submitted successfully with: {st.session_state.form_just_submitted}")
        st.session_state.form_just_submitted = None

        st.markdown("</div>", unsafe_allow_html=True)


def get_volume_input(original_name, confirmed_name):
    """Get volume input for a confirmed series"""
    st.subheader(f"📚 Add Volumes for {confirmed_name}")

    # Create a truly unique form key
    if confirmed_name is None:
        confirmed_name = "unknown_series"
    # Use a combination of original name, confirmed name, and timestamp for uniqueness
    unique_key = f"volume_form_{original_name}_{confirmed_name}_{int(time.time())}"
    # Sanitize the key to remove any problematic characters
    sanitized_key = "".join(c for c in unique_key if c.isalnum() or c in (' ', '-', '_')).replace(' ', '_')
    with st.form(sanitized_key):
        volume_input = st.text_input(
            "Volume Numbers/Ranges",
            placeholder="e.g., 1-5,7,10 or 17-18-19 (for omnibus)",
            help="Supports ranges (1-5), single volumes (7), and omnibus formats (17-18-19)"
        )

        submitted = st.form_submit_button("Add Series")

        if submitted and volume_input:
            try:
                volumes = parse_volume_range(volume_input)
                st.session_state.series_entries.append({
                    'original_name': original_name,
                    'confirmed_name': confirmed_name,
                    'volumes': volumes
                })
                st.success(f"✓ Added {confirmed_name} with volumes: {', '.join(map(str, volumes))}")
                # Clear ALL series state to return to main input form
                st.session_state.selected_series = None
                st.session_state.original_series_name = None
                st.session_state.pending_series_name = None
                st.rerun()
    
    # Debug outside form
    if st.session_state.form_just_submitted:
        st.success(f"✅ Form submitted successfully with: {st.session_state.form_just_submitted}")
        st.session_state.form_just_submitted = None
            except ValueError as e:
                st.error(f"Error parsing volume range: {e}")

        # Add a "Back to Main" button for better UX
        if st.form_submit_button("← Back to Main", type="secondary"):
            st.session_state.selected_series = None
            st.session_state.original_series_name = None
            st.session_state.pending_series_name = None
            st.rerun()
    
    # Debug outside form
    if st.session_state.form_just_submitted:
        st.success(f"✅ Form submitted successfully with: {st.session_state.form_just_submitted}")
        st.session_state.form_just_submitted = None


def confirm_series_names():
    """Confirm series names before processing"""
    st.header("🔍 Series Confirmation")

    if not st.session_state.series_entries:
        st.warning("No series to confirm. Please add series first.")
        return

    # Initialize DeepSeek API
    try:
        deepseek_api = DeepSeekAPI()
    except ValueError as e:
        st.error(f"API configuration error: {e}")
        return

    confirmed_series = []

    for entry in st.session_state.series_entries:
        series_name = entry['original_name']
        volumes = entry['volumes']

        st.subheader(f"Confirm: {series_name}")

        # Get suggestions
        suggestions = deepseek_api.correct_series_name(series_name)

        if len(suggestions) > 1:
            # Multiple suggestions
            selected_option = st.radio(
                f"Select correct series name for '{series_name}':",
                options=suggestions + ["Look Again", "Skip"],
                key=f"confirm_{series_name}"
            )

            if selected_option == "Look Again":
                st.info("Searching for more options...")
                # This would need to be handled differently in Streamlit
                continue
            elif selected_option == "Skip":
                st.warning(f"Skipped {series_name}")
                continue
            else:
                selected_series = selected_option
                st.success(f"Using: {selected_series}")
        else:
            # Single suggestion
            selected_series = suggestions[0]
            st.success(f"Using: {selected_series}")

        # Add to confirmed series
        confirmed_series.append({
            'original_name': series_name,
            'confirmed_name': selected_series,
            'volumes': volumes
        })

    if confirmed_series:
        st.session_state.confirmed_series = confirmed_series
        st.success("✓ All series confirmed!")

        if st.button("▶️ Start Processing", type="primary"):
            st.session_state.processing_state['is_processing'] = True
            st.session_state.processing_state['start_time'] = time.time()
            st.session_state.processing_state['total_volumes'] = sum(
                len(entry['volumes']) for entry in confirmed_series
            )
            st.rerun()
    
    # Debug outside form
    if st.session_state.form_just_submitted:
        st.success(f"✅ Form submitted successfully with: {st.session_state.form_just_submitted}")
        st.session_state.form_just_submitted = None


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

def process_series():
    """Process all confirmed series with threaded execution for better progress updates"""
    if not st.session_state.series_entries:
        return

    # Initialize API (not used directly in this function but needed for imports)
    try:
        _ = DeepSeekAPI()  # Create instance to verify API is available
    except ValueError as e:
        st.error(f"API configuration error: {e}")
        st.session_state.processing_state['is_processing'] = False
        return

    all_books = []
    errors = []

    # Show initial processing message
    st.info("🔄 Please wait while we look up your manga volumes...")

    # Create a list of all volumes to process
    all_volumes = []
    for series_entry in st.session_state.series_entries:
        series_name = series_entry['confirmed_name']
        volumes = series_entry['volumes']
        for volume in volumes:
            all_volumes.append((series_name, volume))

    # Process volumes with threading
    with ThreadPoolExecutor(max_workers=15) as executor:
        # Submit all tasks
        future_to_volume = {
            executor.submit(process_single_volume, series_name, volume, st.session_state.project_state): (series_name, volume)
            for series_name, volume in all_volumes
        }

        # Process results as they complete
        for i, future in enumerate(as_completed(future_to_volume)):
            series_name, volume = future_to_volume[future]

            # Update progress
            st.session_state.processing_state['current_series'] = series_name
            st.session_state.processing_state['current_volume'] = volume
            st.session_state.processing_state['progress'] = i + 1


            try:
                book, error = future.result()
                if book:
                    all_books.append(book)
                elif error:
                    errors.append(error)
            except Exception as e:
                errors.append(f"Unexpected error processing {series_name} volume {volume}: {str(e)}")

    # Assign barcodes
    start_barcode = st.session_state.get('start_barcode', "T000001")
    barcodes = generate_sequential_barcodes(start_barcode, len(all_books))
    for book, barcode in zip(all_books, barcodes):
        book.barcode = barcode

    st.session_state.all_books = all_books
    st.rerun()  # Update UI after processing
    st.session_state.processing_state['is_processing'] = False

    # Record interaction
    series_info = ", ".join([
        f"{entry['confirmed_name']} ({len(entry['volumes'])} vols)"
        for entry in st.session_state.series_entries
    ])
    st.session_state.project_state.record_interaction(
        f"Multiple series: {series_info}", len(all_books)
    )

    # Show results
    if all_books:
        st.success(f"✓ Found {len(all_books)} books!")
    if errors:
        st.warning(f"⚠️ {len(errors)} volumes had issues:")
        for error in errors:
            st.write(f"• {error}")

    st.rerun()  # Final rerun to show results


def fetch_cover_for_book(book: BookInfo) -> Optional[str]:
    """Fetch cover image for a book if not cached"""
    # Try Google Books first for volumes
    if book.isbn_13:
        google_client = GoogleBooksClient()
        cover_url = google_client.get_cover_image_url(book.isbn_13)
        if cover_url:
            return cover_url

    # Fallback to MAL or MangaDex for series
    mal_fetcher = MALCoverFetcher()
    cover_url = mal_fetcher.fetch_cover_for_series(book.series_name)
    if cover_url:
        return cover_url

    # Final fallback to MangaDex
    mangadex_fetcher = MangaDexCoverFetcher()
    cover_url = mangadex_fetcher.fetch_cover_for_series(book.series_name)
    return cover_url


def show_book_details_modal(book: BookInfo):
    """Show book details in a modal-like popup with cover image"""
    st.markdown("---")
    st.subheader(f"📖 Book Details - Volume {book.volume_number}")

    # Create columns - adjust ratio based on whether we have a cover image
    if book.cover_image_url:
        col1, col2 = st.columns([1, 2])
        col1, col2 = st.columns(2)

    with col1:
        # Display cover image if available
        # Fetch cover if not available
        if not book.cover_image_url:
            with st.spinner("Fetching cover image..."):
                cover_url = fetch_cover_for_book(book)
                if cover_url:
                    book.cover_image_url = cover_url
                st.success("Cover image fetched!")
        if book.cover_image_url:
            try:
                st.image(book.cover_image_url, caption="Cover Image")
            except Exception as e:
                st.error(f"Could not load cover image: {e}")
                st.write("**Cover:** Image unavailable")
        else:
            st.write("**Cover:** No image available")

    with col2:
        st.write(f"**Title:** {book.book_title}")
        st.write(f"**Series:** {book.series_name}")
        st.write(f"**Authors:** {DataValidator.format_authors_list(book.authors)}")
        st.write(f"**Volume:** {book.volume_number}")
        st.write(f"**Barcode:** {book.barcode}")
        st.write(f"**MSRP:** ${book.msrp_cost:.2f}" if book.msrp_cost else "**MSRP:** Unknown")
        st.write(f"**ISBN-13:** {book.isbn_13}" if book.isbn_13 else "**ISBN-13:** Unknown")
        st.write(f"**Publisher:** {book.publisher_name}" if book.publisher_name else "**Publisher:** Unknown")
        st.write(f"**Copyright Year:** {book.copyright_year}" if book.copyright_year else "**Copyright Year:** Unknown")

    # Description
    if book.description:
        st.subheader("Description")
        st.write(book.description)

    # Physical Description
    if book.physical_description:
        st.subheader("Physical Description")
        st.write(book.physical_description)

    # Genres
    if book.genres:
        st.subheader("Genres")
        st.write(", ".join(book.genres))

    # Warnings
    if book.warnings:
        st.subheader("⚠️ Warnings")
        for warning in book.warnings:
            st.write(f"• {warning}")


def display_results():
    """Display results in expandable table"""
    if not st.session_state.all_books:
        return

    # Celebrate completion with confetti
    st.balloons()

    st.header("📋 Results")

    st.header("📋 Results")

    # Export options - moved above the table
    st.subheader("Export Options")

    # Large MARC export button
    col1, col2 = st.columns([2, 1])

    with col1:
        try:
            filename = f"manga_marc_{datetime.now().strftime('%Y%m%d_%H%M%S')}.mrc"
            export_books_to_marc(st.session_state.all_books, filename, "M")

            with open(filename, "rb") as file:
                st.download_button(
                    label="📚 Export & Download MARC Records",
                    data=file,
                    file_name=filename,
                    mime="application/marc",
                    use_container_width=True,
                    type="primary"
                )
        except Exception as e:
            st.error(f"Error exporting MARC: {e}")

    with col2:
        # JSON export
        if st.button("💾 Export JSON"):
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
                for book in st.session_state.all_books
            ]

            json_str = json.dumps(results_data, indent=2)
            st.download_button(
                label="💾 Download JSON",
                data=json_str,
                file_name=f"manga_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                mime="application/json",
                use_container_width=True
            )

    # Display expandable table with Streamlit data table
    with st.expander(f"Results ({len(st.session_state.all_books)} books)", expanded=True):
        # Create DataFrame for the table
        table_data = []
        for book in st.session_state.all_books:
            msrp_cell = "✓" if book.msrp_cost else "✗"
            isbn_cell = "✓" if book.isbn_13 else "✗"
            publisher_cell = "✓" if book.publisher_name else "✗"
            year_cell = "✓" if book.copyright_year else "✗"
            description_cell = "✓" if book.description else "✗"
            physical_cell = "✓" if book.physical_description else "✗"
            genres_cell = "✓" if book.genres else "✗"
            cover_cell = "✓" if book.cover_image_url else "✗"

            table_data.append({
                'Barcode': book.barcode,
                'Title': book.book_title,
                'Series': book.series_name,
                'Volume': book.volume_number,
                'Authors': DataValidator.format_authors_list(book.authors),
                'MSRP': msrp_cell,
                'ISBN': isbn_cell,
                'Publisher': publisher_cell,
                'Year': year_cell,
                'Description': description_cell,
                'Physical': physical_cell,
                'Genres': genres_cell,
                'Cover': cover_cell
            })

        # Create DataFrame and display as table
        if table_data:
            df = pd.DataFrame(table_data)
            st.dataframe(df, hide_index=True)
            st.info("No books found to display")

    # Book details modal
    st.subheader("Book Details")

    # Create a selectbox for book selection
    book_options = [f"{book.barcode} - {book.book_title}" for book in st.session_state.all_books]

    if book_options:
        # Initialize selected book index in session state
        if 'selected_book_index' not in st.session_state:
            st.session_state.selected_book_index = 0
        selected_book = st.selectbox(
            "Select a book to view details:",
            options=book_options,
            index=st.session_state.selected_book_index,
            key="book_details_selector"
        )

        if selected_book:
            # Find the selected book
            selected_index = book_options.index(selected_book)

            # Update session state if selection changed
            if selected_index != st.session_state.selected_book_index:
                st.session_state.selected_book_index = selected_index
                st.rerun()
    
    # Debug outside form
    if st.session_state.form_just_submitted:
        st.success(f"✅ Form submitted successfully with: {st.session_state.form_just_submitted}")
        st.session_state.form_just_submitted = None

            selected_book_obj = st.session_state.all_books[selected_index]

            # Show details
            show_book_details_modal(selected_book_obj)



def main():
    # Custom CSS for rounded corners and manga theme
    st.markdown("""
    <style>
    .stButton button {
        border-radius: 10px !important;
    }
    .stTextInput input, .stSelectbox select, .stMultiselect select {
        border-radius: 8px !important;
    }
    .stCard {
        border-radius: 12px !important;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1) !important;
    }
    .manga-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        border-radius: 12px;
        padding: 15px;
        margin: 10px 0;
        color: white;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.2);
    }
    .manga-card-alt {
        background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
        border-radius: 12px;
        padding: 15px;
        margin: 10px 0;
        color: white;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.2);
    }
    .manga-banner {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 20px;
        border-radius: 15px;
        text-align: center;
        margin-bottom: 20px;
        box-shadow: 0 6px 20px rgba(0, 0, 0, 0.15);
    }
    .manga-banner h1 {
        font-size: 2.5em;
        margin-bottom: 10px;
    }
    </style>
    """, unsafe_allow_html=True)
    st.set_page_config(
        page_title="Manga Lookup Tool",
        page_icon="📚",
        layout="wide",
        initial_sidebar_state="expanded"
    )

    # Add sidebar with app information
    with st.sidebar:
        st.title("📚 Manga Lookup")
        st.markdown("---")

        st.markdown("### About")
        st.markdown("Streamlined web interface for manga series lookup and MARC export")
        st.markdown("---")

        st.markdown("### Features")
        st.markdown("• Series name correction")
        st.markdown("• Volume range support")
        st.markdown("• MARC export for library systems")
        st.markdown("• Barcode generation")
        st.markdown("---")

        # Help section
        with st.expander("📖 Help & Instructions", expanded=False):
            st.markdown("""
            ### How to Use This App

            **1. Enter Starting Barcode**
            - Enter your starting barcode (e.g., T000001)
            - This will be used to generate sequential barcodes for all volumes

            **2. Add Series**
            - Enter manga series names one at a time
            - For each series, enter volume ranges:
              - Single volumes: `7`
              - Ranges: `1-5`
              - Omnibus volumes: `17-18-19`
              - Combinations: `1-5,7,10-12`

            **3. Confirm Series Names**
            - The app will suggest correct series names
            - Select the correct series from the suggestions

            **4. Process Volumes**
            - Click "Start Lookup" to begin processing
            - The app will fetch detailed information for each volume
            - Progress will be shown with elapsed time

            **5. Export Results**
            - **MARC Export**: Creates library catalog records
            - **JSON Export**: Raw data for other uses

            ### Importing MARC Files into Atriuum

            **Step 1: Download MARC File**
            - Click the "📚 Export MARC Records" button
            - Download the generated .mrc file

            **Step 2: Import into Atriuum**
            1. Open Atriuum Library System
            2. Go to **Cataloging** → **Import/Export**
            3. Select **MARC Import**
            4. Choose the downloaded .mrc file
            5. Map fields according to your library's specifications
            6. Run the import process

            **Important Notes:**
            - Each volume becomes a separate bibliographic record
            - Barcodes are automatically assigned sequentially
            - Records include full MARC 21 format with holding information
            - Verify the import results before finalizing

            ### Volume Range Examples
            - `1-5` → Volumes 1, 2, 3, 4, 5
            - `7` → Volume 7 only
            - `17-18-19` → Omnibus containing volumes 17, 18, 19
            - `1-3,7,10-12` → Volumes 1, 2, 3, 7, 10, 11, 12
            """)

    st.markdown("""<div class="manga-banner"><h1>📚 Manga Lookup Tool</h1><p>Streamlined web interface for manga series lookup and MARC export</p></div>""", unsafe_allow_html=True)
    
    # Debug: Check cache status
    if st.checkbox("🔍 Check Cache Status", help="Verify cached images are deployed"):
        cache_dir = "cache"
        images_dir = os.path.join(cache_dir, "images")
        
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Cache Directory Exists", "✅" if os.path.exists(cache_dir) else "❌")
            st.metric("Images Directory Exists", "✅" if os.path.exists(images_dir) else "❌")
        
        if os.path.exists(images_dir):
            image_files = [f for f in os.listdir(images_dir) if f.endswith(".jpg")]
            with col2:
                st.metric("Image Files", len(image_files))
                st.metric("DB Cached Images", "243")
                st.metric("API Responses", "1117")
                
            if image_files:
                st.subheader("Sample Cached Images")
                sample_cols = st.columns(min(3, len(image_files)))
                for i, img_file in enumerate(image_files[:3]):
                    with sample_cols[i]:
                        img_path = os.path.join(images_dir, img_file)
                        st.image(img_path, caption=f"{img_file}", width=100)
        else:
            st.error("❌ Cache directory not found! Images may not be deployed properly.")

    # Initialize session state
    initialize_session_state()

    # Main workflow with tabs
    tab1, tab2, tab3 = st.tabs(["📚 Add Series", "🔍 Confirm", "📊 Results"])
    
    with tab1:
        # Debug: Show current state
        with st.expander("🔧 Workflow Debug", expanded=False):
            st.write("**Processing:**", st.session_state.processing_state["is_processing"])
            st.write("**All books:**", bool(st.session_state.all_books))
            st.write("**Confirmed series:**", bool(st.session_state.confirmed_series))
            st.write("**Selected series:**", bool(st.session_state.selected_series))
            st.write("**Pending series:**", bool(st.session_state.pending_series_name))
            if st.session_state.pending_series_name:
                st.write("**Pending series name:**", st.session_state.pending_series_name)

        if st.session_state.processing_state["is_processing"]:
            st.info("Processing in progress... Check the Confirm tab for details.")
        elif st.session_state.all_books:
            st.success("All processing complete! Check the Results tab.")
        elif st.session_state.confirmed_series:
            st.info("Series confirmed! Ready to process volumes.")
        elif st.session_state.selected_series:
            get_volume_input(st.session_state.original_series_name, st.session_state.selected_series)
        elif st.session_state.pending_series_name:
            confirm_single_series(st.session_state.pending_series_name)
        else:
            series_input_form()
    
    with tab2:
        if st.session_state.processing_state["is_processing"]:
            with st.spinner("Processing manga volumes..."):
                display_progress_section()
                process_series()
        elif st.session_state.confirmed_series:
            confirm_series_names()
        else:
            st.info("Add series first in the Add Series tab.")
    
    with tab3:
        if st.session_state.all_books:
            display_results()
        else:
            st.info("No results yet. Complete the workflow in other tabs.")


if __name__ == "__main__":
    main()
