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
from typing import List, Dict, Optional
import base64
import requests

# Import existing core logic
from manga_lookup import (
    BookInfo, DeepSeekAPI, DataValidator, ProjectState,
    parse_volume_range, generate_sequential_barcodes, process_book_data
)

# Import MARC exporter
from marc_exporter import export_books_to_marc


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


def get_duck_animation():
    """Get duck drinking coffee animation (placeholder)"""
    # This will be replaced with an actual animated GIF
    # For now, using emojis that can be animated with CSS
    return "🦆☕"


def display_duck_animation():
    """Display animated duck with CSS"""
    st.markdown("""
    <style>
    @keyframes drink-coffee {
        0% { transform: translateY(0px); }
        50% { transform: translateY(-5px); }
        100% { transform: translateY(0px); }
    }
    .duck-animation {
        animation: drink-coffee 2s ease-in-out infinite;
        font-size: 3em;
        text-align: center;
    }
    </style>
    <div class="duck-animation">🦆☕</div>
    """, unsafe_allow_html=True)


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
        else:
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
            eta = calculate_eta(state['start_time'], progress, total)
            st.metric("ETA", eta)

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

    # Starting barcode - only show if not already set
    if 'start_barcode' not in st.session_state or not st.session_state.start_barcode:
        st.markdown("<i style='color: gray;'>(e.g. T000001)</i>", unsafe_allow_html=True)
        start_barcode = st.text_input(
            "Starting Barcode",
            placeholder="Enter starting barcode",
            help="Enter starting barcode (e.g., T000001 or MANGA001)"
        )
        if start_barcode:
            st.session_state.start_barcode = start_barcode

    # Series input section
    st.subheader("Add Series")

    with st.form("series_form", clear_on_submit=True):
        # Make series name entry ordinal
        series_count = len(st.session_state.series_entries) + 1
        ordinal_text = "First" if series_count == 1 else "Second" if series_count == 2 else "Third" if series_count == 3 else f"{series_count}th"

        series_name = st.text_input(f"Enter {ordinal_text} Series Name")

        submitted = st.form_submit_button("Confirm Series Name")

        if submitted and series_name:
            # Store the series name for confirmation
            st.session_state.pending_series_name = series_name
            st.rerun()

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

        st.subheader("📋 Current Series")

        for i, entry in enumerate(st.session_state.series_entries):
            with st.container():
                st.markdown('<div class="cyan-background">', unsafe_allow_html=True)

                # Series header
                col1, col2 = st.columns([4, 1])
                with col1:
                    st.write(f"**Series {i+1}: {entry['confirmed_name']}**")
                with col2:
                    if st.button("🗑️ Remove", key=f"remove_{i}"):
                        st.session_state.series_entries.pop(i)
                        st.rerun()

                # Create table with volume numbers and barcodes
                if 'all_books' in st.session_state and st.session_state.all_books:
                    # Get books for this specific series
                    series_books = [book for book in st.session_state.all_books if book.series_name == entry['confirmed_name']]
                    if series_books:
                        # Create table data
                        table_data = []
                        for book in series_books:
                            table_data.append({
                                'Volume': book.volume_number,
                                'Barcode': book.barcode if hasattr(book, 'barcode') and book.barcode else 'Pending'
                            })

                        # Display as table
                        if table_data:
                            df = pd.DataFrame(table_data)
                            st.dataframe(df, use_container_width=True, hide_index=True)
                    else:
                        st.write(f"*Volumes: {', '.join(map(str, entry['volumes']))} (not yet processed)*")
                else:
                    st.write(f"*Volumes: {', '.join(map(str, entry['volumes']))} (not yet processed)*")

                st.markdown('</div>', unsafe_allow_html=True)

    # Start processing button
    if st.session_state.series_entries:
        if st.button("🚀 Start Lookup", type="primary", use_container_width=True):
            st.session_state.processing_state['is_processing'] = True
            st.session_state.processing_state['start_time'] = time.time()
            st.session_state.processing_state['total_volumes'] = sum(
                len(entry['volumes']) for entry in st.session_state.series_entries
            )
            st.rerun()


def confirm_single_series(series_name):
    """Confirm a single series name with series information in separate cards"""
    st.header(f"🔍 Confirm: {series_name}")

    # Initialize DeepSeek API
    try:
        deepseek_api = DeepSeekAPI()
    except ValueError as e:
        st.error(f"API configuration error: {e}")
        return

    # Get suggestions
    suggestions = deepseek_api.correct_series_name(series_name)

    if len(suggestions) > 1:
        # Multiple suggestions - display in separate cards
        st.write("Select the correct series name:")

        # Create columns for the cards
        cols = st.columns(min(3, len(suggestions)))

        for i, suggestion in enumerate(suggestions):
            with cols[i % len(cols)]:
                # Create a card container
                with st.container():
                    # Show title immediately
                    st.subheader(suggestion)

                    # Get series information
                    series_info = deepseek_api._get_series_info(suggestion)

                    # Display series information
                    if series_info:
                        st.write(f"**Info:** {series_info}")
                    else:
                        st.write("*No additional information available*")

                    # Make the entire card clickable
                    if st.button(f"✓ Select {suggestion}", key=f"select_{i}", use_container_width=True):
                        # Store selected series for volume input
                        st.session_state.selected_series = suggestion
                        st.session_state.original_series_name = series_name
                        st.rerun()

                    st.markdown("---")

        # Look Again and Skip options
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🔄 Look Again", use_container_width=True):
                st.info("Searching for more options...")
                # Clear pending series to restart
                st.session_state.pending_series_name = None
                st.rerun()

        with col2:
            if st.button("⏭️ Skip", use_container_width=True):
                st.warning(f"Skipped {series_name}")
                st.session_state.pending_series_name = None
                st.rerun()
    else:
        # Single suggestion
        selected_series = suggestions[0]
        st.success(f"✓ Using: {selected_series}")

        # Show series information in a card
        with st.container():
            col1, col2 = st.columns([1, 3])
            with col1:
                # Display series icon
                st.markdown("📚")
                st.caption("Manga Series")

            with col2:
                st.subheader(selected_series)

                # Get and display series information
                series_info = deepseek_api._get_series_info(selected_series)
                if series_info:
                    st.write(f"**Series Info:** {series_info}")

                if st.button("✓ Confirm and Add Volumes", type="primary", use_container_width=True):
                    # Store selected series for volume input
                    st.session_state.selected_series = selected_series
                    st.session_state.original_series_name = series_name
                    st.rerun()


def get_volume_input(original_name, confirmed_name):
    """Get volume input for a confirmed series"""
    st.subheader(f"📚 Add Volumes for {confirmed_name}")

    with st.form("volume_form"):
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
            except ValueError as e:
                st.error(f"Error parsing volume range: {e}")

        # Add a "Back to Main" button for better UX
        if st.form_submit_button("← Back to Main", type="secondary"):
            st.session_state.selected_series = None
            st.session_state.original_series_name = None
            st.session_state.pending_series_name = None
            st.rerun()


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


def process_series():
    """Process all confirmed series"""
    if not st.session_state.series_entries:
        return

    # Initialize API
    try:
        deepseek_api = DeepSeekAPI()
    except ValueError as e:
        st.error(f"API configuration error: {e}")
        st.session_state.processing_state['is_processing'] = False
        return

    all_books = []
    progress = 0

    # Show initial processing message
    st.info("🔄 Please wait while we look up your manga volumes...")

    # Add elapsed time display
    if st.session_state.processing_state['start_time']:
        elapsed = time.time() - st.session_state.processing_state['start_time']
        st.write(f"**Elapsed time:** {int(elapsed)} seconds")

    # Use Streamlit's experimental_rerun to avoid infinite loops
    for series_entry in st.session_state.series_entries:
        series_name = series_entry['confirmed_name']
        volumes = series_entry['volumes']

        st.session_state.processing_state['current_series'] = series_name

        series_books = []
        for volume in volumes:
            st.session_state.processing_state['current_volume'] = volume
            progress += 1
            st.session_state.processing_state['progress'] = progress

            # Update progress display - use placeholder for now
            st.write(f"Processing: **{series_name}** - Volume **{volume}** ({progress}/{st.session_state.processing_state['total_volumes']})")

            # Get book data
            try:
                book_data = deepseek_api.get_book_info(
                    series_name, volume, st.session_state.project_state
                )

                if book_data:
                    book = process_book_data(book_data, volume)
                    series_books.append(book)
                    st.success(f"✓ Found volume {volume}")
                else:
                    st.warning(f"⚠️ Volume {volume} not found")
            except Exception as e:
                st.error(f"❌ Error processing volume {volume}: {str(e)}")

        all_books.extend(series_books)

    # Assign barcodes
    # Get start barcode from user input or use default
    start_barcode = st.session_state.get('start_barcode', "T000001")
    barcodes = generate_sequential_barcodes(start_barcode, len(all_books))
    for book, barcode in zip(all_books, barcodes):
        book.barcode = barcode

    st.session_state.all_books = all_books
    st.session_state.processing_state['is_processing'] = False

    # Record interaction
    series_info = ", ".join([
        f"{entry['confirmed_name']} ({len(entry['volumes'])} vols)"
        for entry in st.session_state.series_entries
    ])
    st.session_state.project_state.record_interaction(
        f"Multiple series: {series_info}", len(all_books)
    )

    st.success(f"✓ Found {len(all_books)} books!")
    st.rerun()  # Final rerun to show results


def show_book_details_modal(book: BookInfo):
    """Show book details in a modal-like popup"""
    st.markdown("---")
    st.subheader(f"📖 Book Details - Volume {book.volume_number}")

    col1, col2 = st.columns(2)

    with col1:
        st.write(f"**Title:** {book.book_title}")
        st.write(f"**Series:** {book.series_name}")
        st.write(f"**Authors:** {DataValidator.format_authors_list(book.authors)}")
        st.write(f"**Volume:** {book.volume_number}")
        st.write(f"**Barcode:** {book.barcode}")

    with col2:
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

    st.header("📋 Results")

    # Create DataFrame for display
    books_data = []
    for i, book in enumerate(st.session_state.all_books):
        books_data.append({
            'Barcode': book.barcode,
            'Title': book.book_title,
            'Series': book.series_name,
            'Volume': book.volume_number,
            'Authors': DataValidator.format_authors_list(book.authors),
            'MSRP': '✓' if book.msrp_cost else '✗',
            'ISBN': '✓' if book.isbn_13 else '✗',
            'Publisher': '✓' if book.publisher_name else '✗',
            'Year': '✓' if book.copyright_year else '✗',
            'Description': '✓' if book.description else '✗',
            'Physical': '✓' if book.physical_description else '✗',
            'Genres': '✓' if book.genres else '✗',
            'Index': i  # Store index for modal
        })

    df = pd.DataFrame(books_data)
    display_df = df.drop('Index', axis=1)  # Don't show index column

    # Display expandable table
    with st.expander(f"Results ({len(df)} books)", expanded=True):
        st.dataframe(
            display_df,
            use_container_width=True,
            hide_index=True
        )

    # Book details modal
    st.subheader("Book Details")

    # Create a selectbox for book selection
    book_options = [f"{book.barcode} - {book.book_title}" for book in st.session_state.all_books]

    if book_options:
        selected_book = st.selectbox(
            "Select a book to view details:",
            options=book_options,
            key="book_details_selector"
        )

        if selected_book:
            # Find the selected book
            selected_index = book_options.index(selected_book)
            selected_book_obj = st.session_state.all_books[selected_index]

            # Show details
            show_book_details_modal(selected_book_obj)

    # Export options
    st.subheader("Export Options")

    col1, col2 = st.columns(2)

    with col1:
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
                label="Download JSON",
                data=json_str,
                file_name=f"manga_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                mime="application/json"
            )

    with col2:
        # MARC export
        if st.button("📚 Export MARC"):
            try:
                filename = f"manga_marc_{datetime.now().strftime('%Y%m%d_%H%M%S')}.mrc"
                export_books_to_marc(st.session_state.all_books, filename, "M")

                with open(filename, "rb") as file:
                    st.download_button(
                        label="Download MARC",
                        data=file,
                        file_name=filename,
                        mime="application/marc"
                    )
            except Exception as e:
                st.error(f"Error exporting MARC: {e}")


def main():
    """Main Streamlit app"""
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

    st.title("📚 Manga Lookup Tool")
    st.markdown("Streamlined web interface for manga series lookup and MARC export")

    # Initialize session state
    initialize_session_state()

    # Main workflow
    if st.session_state.processing_state['is_processing']:
        # Processing in progress
        st.header("🔄 Processing...")
        display_progress_section()
        process_series()
    elif st.session_state.all_books:
        # Results available
        display_results()
    elif st.session_state.confirmed_series:
        # Ready to process
        confirm_series_names()
    elif st.session_state.selected_series:
        # Volume input phase
        get_volume_input(st.session_state.original_series_name, st.session_state.selected_series)
    elif st.session_state.pending_series_name:
        # Series confirmation phase
        confirm_single_series(st.session_state.pending_series_name)
    else:
        # Input phase
        series_input_form()


if __name__ == "__main__":
    main()