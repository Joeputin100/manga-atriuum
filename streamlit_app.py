# Manga Lookup Tool - Dev Version
# Trivial change to trigger redeploy
# Trivial change to trigger redeploy
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
import sys

try:
    import streamlit as st
except ImportError:
    sys.exit(1)

import html
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

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
        return None
    except Exception:
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
    except Exception:
        pass

    # Fallback to MAL
    try:
        mal_fetcher = MALCoverFetcher()
        cover_url = mal_fetcher.fetch_cover(book.series_name, book.volume_number)
        if cover_url:
            return cover_url
    except Exception:
        pass

    # Fallback to MangaDex
    try:
        mangadex_fetcher = MangaDexCoverFetcher()
        cover_url = mangadex_fetcher.fetch_cover(book.series_name, book.volume_number)
        if cover_url:
            return cover_url
    except Exception:
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
        return None, f"Volume {volume} not found"
    except Exception as e:
        return None, f"Error processing volume {volume}: {e!s}"


def process_series():
    """Process all confirmed series with threaded execution for better progress updates"""
    # Create a list of all volumes to process
    all_volumes = []
    for series_entry in st.session_state.series_entries:
        series_name = series_entry["confirmed_name"]
        volumes = series_entry["volumes"]
        for volume in volumes:
            all_volumes.append((series_name, volume))

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
    if elapsed < 60:
        return f"{int(elapsed)} seconds"
    if elapsed < 3600:
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
        if eta_seconds < 3600:
            return f"{int(eta_seconds/60)} minutes"
        return f"{int(eta_seconds/3600)} hours"
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
            # Show barcode increment pattern dynamically
            if start_barcode_input:
                sample_barcodes = generate_sequential_barcodes(start_barcode_input, 5)
                st.write(f"Barcode pattern: {', '.join(sample_barcodes)}")
            if start_barcode_input:
                st.session_state.start_barcode = start_barcode_input
                # Show barcode increment pattern
                sample_barcodes = generate_sequential_barcodes(start_barcode_input, 5)
                st.success(
                    f"Barcode pattern confirmed: {', '.join(sample_barcodes)}...",
                )
                st.session_state.barcode_confirmed = True
                st.rerun()
        if st.session_state.get("barcode_confirmed", False):
            st.subheader("Add Series")
            st.write(f"Barcode pattern: {st.session_state.get(barcode_pattern, )}")

        # Make series name entry ordinal
        series_count = len(st.session_state.series_entries) + 1
        ordinal_text = (
            "1st"
            if series_count == 1
            else (
                "2nd"
                if series_count == 2
                else "3rd" if series_count == 3 else f"{series_count}th"
            )
        )
        series_name = st.text_input(
            f"Enter {ordinal_text} Series Name",
            help="Enter the manga series name (e.g., Naruto, One Piece, Death Note)",
        )
        if st.button("Confirm Series Name", key="confirm_series"):
            if series_name:
                st.session_state.pending_series_name = series_name
                st.info("Confirming series name, searching for matches...")
                st.rerun()
            else:
                st.error("Please enter a series name")

    # Display current series with cyan background
    if st.session_state.series_entries and any(
        entry.get("volumes", []) for entry in st.session_state.series_entries
    ):
        st.markdown(
            """
        <style>
        .cyan-background {
            background-color: #e0f7fa;
            padding: 15px;
            border-radius: 10px;
            border: 1px solid #80deea;
            margin-bottom: 10px;
        }
        </style>
        """,
            unsafe_allow_html=True,
        )

        # Display series in a grid of cards
        cols = st.columns(2)  # 2 columns for cards

        for i, entry in enumerate(st.session_state.series_entries):
            col_idx = i % 2
            with cols[col_idx]:
                # Use Streamlit components instead of HTML for better compatibility
                st.markdown(f"### 📚 {entry['confirmed_name']}")
                st.caption(f"Vol: {len(entry['volumes'])}")

                # Try to get cover image
                cover_url = None
                # Create a dummy book object to get series cover
                try:
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
                        warnings=[],
                    )
                    cover_url = fetch_cover_for_book(dummy_book)
                except Exception:
                    pass

                if cover_url:
                    st.image(cover_url, width=100)

                    st.write(f"**Volumes:** {', '.join(map(str, entry['volumes']))}")
                # Volume input
                col1, col2 = st.columns(2)
                with col1:
                    volume_input = st.text_input(
                        f"Volumes for {entry['confirmed_name']}",
                        placeholder="1-5, 10",
                        key=f"volumes_{i}",
                    )
                with col2:
                    if st.button("Add Volumes", key=f"add_vol_{i}") and volume_input:
                        try:
                            volumes = parse_volume_range(volume_input)
                            entry["volumes"] = volumes
                            st.success(
                            f"You have successfully added volumes {', '.join(map(str, volumes))} to {entry['confirmed_name']}!",
                        )
                            st.balloons()
                        except ValueError as e:
                            st.error(f"Invalid volume range: {e}")

                # Remove button
                if st.button("🗑️ Remove", key=f"remove_{i}"):
                    st.session_state.series_entries.pop(i)
    st.divider()

    #    # Start processing button
    if (
        st.session_state.series_entries
        and any(entry.get("volumes", []) for entry in st.session_state.series_entries)
        and st.button("🚀 Start Lookup", type="primary")
    ):
        # Calculate total volumes
        total_volumes = sum(
            len(entry["volumes"]) for entry in st.session_state.series_entries
        )

        # Initialize processing state
        st.session_state.processing_state = {
            "is_processing": True,
            "current_series": None,
            "current_volume": None,
            "progress": 0,
            "total_volumes": total_volumes,
            "start_time": time.time(),
        }

        # Start processing

    state = st.session_state.processing_state
    if state["is_processing"]:

        progress = state["progress"]
        total = state["total_volumes"]

        # Progress bar
        progress_percent = int((progress / total) * 100) if total > 0 else 0
        st.progress(progress_percent / 100)

        # Progress info
        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric("Progress", f"{progress}/{total}")

        with col2:
            if state["start_time"]:
                elapsed = calculate_elapsed_time(state["start_time"])
                st.metric("Elapsed Time", elapsed)

        with col3:
            # Animated duck
            display_duck_animation()
            st.caption("Processing...")

    # Current task info
    if state["current_series"]:
        st.info(
            f"Processing: **{state['current_series']}** - Volume **{state['current_volume']}**",
        )


def confirm_single_series(series_name):
    """Confirm a single series name with series information in separate cards"""
    st.header(f"🔍 Confirm: {series_name}")

    # Initialize DeepSeek API
    st.info("Searching for series matches...")
    try:
        deepseek_api = DeepSeekAPI()
    except ValueError:
        st.error("API configuration error. Please check your environment variables.")
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
                # Fetch series details
                try:
                    book_data = deepseek_api.get_book_info(
                        suggestion,
                        1,
                        st.session_state.project_state,
                    )
                    st.write(
                        f"Book data keys: {list(book_data.keys()) if book_data else None}",
                    )
                    authors = book_data.get("authors", []) if book_data else []
                    description = book_data.get("description", "") if book_data else ""
                    total_volumes = (
                        book_data.get("number_of_extant_volumes", "Unknown")
                        if book_data
                        else "Unknown"
                    )
                except Exception as e:
                    st.error(f"API Error: {e!s}")
                    authors = []
                    description = "Unable to fetch details"
                    total_volumes = "Unknown"
                card_colors = [
                    "linear-gradient(135deg, #667eea 0%, #764ba2 100%)",
                    "linear-gradient(135deg, #f093fb 0%, #f5576c 100%)",
                    "linear-gradient(135deg, #4facfe 0%, #00f2fe 100%)",
                    "linear-gradient(135deg, #43e97b 0%, #38f9d7 100%)",
                    "linear-gradient(135deg, #fa709a 0%, #fee140 100%)",
                    "linear-gradient(135deg, #a8edea 0%, #fed6e3 100%)",
                ]
                card_color = card_colors[i % len(card_colors)]

                st.markdown(
                    f"""
                <div style="
                    background: {card_color};
                    border-radius: 12px;
                    padding: 20px;
                    margin: 10px 0;
                    color: white;
                    box-shadow: 0 4px 15px rgba(0, 0, 0, 0.2);
                    border: 2px solid rgba(255, 255, 255, 0.3);
                ">
                """,
                    unsafe_allow_html=True,
                )

                # Show title immediately
                st.subheader(suggestion)

                # Try to get cover image
                try:
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
                        warnings=[],
                    )
                    st.markdown(
                        '<p style="font-size: 10px; color: gray;">Note: Covers may vary for different languages, editions, and reprintings.</p>',
                        unsafe_allow_html=True,
                    )
                    cover_url = fetch_cover_for_book(dummy_book)
                except Exception:
                    pass

                if cover_url:
                    st.image(cover_url, width=100)
                if authors:
                    st.write(f"**Authors:** {', '.join(authors)}")
                if description:
                    desc_text = (
                        description[:150] + "..."
                        if len(description) > 150
                        else description
                    )
                    st.write(f"**Description:** {desc_text}")
                    st.write(f"**Total Volumes:** {total_volumes}")
                # Selection button
                if st.button(f"Select {suggestion}", key=f"select_{i}"):
                    st.session_state.pending_series_name = None
                    # Add to confirmed series
                    st.session_state.series_entries.append(
                        {
                            "original_name": series_name,
                            "confirmed_name": suggestion,
                            "volumes": [],
                        },
                    )
                    st.success(f"Selected: {suggestion}")

    elif len(suggestions) == 1:
        # Single suggestion - auto-confirm
        confirmed_name = suggestions[0]
        st.success(f"Found: {confirmed_name}")

        # Add to confirmed series
        st.session_state.series_entries.append(
            {
                "original_name": series_name,
                "confirmed_name": confirmed_name,
                "volumes": [],
            },
        )

        # Clear pending
        st.session_state.pending_series_name = None

    else:
        st.error("No suggestions found. Please try a different series name.")


def main():
    # Main application entry point
    """Main application logic"""
    st.title("📚 Manga Lookup Tool")

    # Initialize session state
    initialize_session_state()
    # Reset processing state if stuck
    if (
        st.session_state.processing_state.get("is_processing", False)
        and not st.session_state.all_books
    ):
        st.session_state.processing_state["is_processing"] = False

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

        # Group books by series
        from collections import defaultdict

        series_groups = defaultdict(list)
        for book in st.session_state.all_books:
            series_groups[book.series_name].append(book)

        # Sort series and volumes
        series_colors = ["#f0f8ff", "#fff8dc", "#f5f5f5", "#e6e6fa"]
        color_index = 0
        for series_name in sorted(series_groups.keys()):
            books = sorted(series_groups[series_name], key=lambda x: x.volume_number)

            # Series header with background
            st.markdown(
                f'<div style="background-color:{series_colors[color_index % len(series_colors)]}; padding:10px; border-radius:5px;"><h3>📚 {html.escape(series_name)}</h3></div>',
                unsafe_allow_html=True,
            )
            color_index += 1

            # Table header
            col1, col2, col3, col4, col5, col6 = st.columns([1, 3, 2, 2, 2, 2])
            col1.write("**Vol**")
            col2.write("**Cover & Title**")
            col3.write("**Genre/Subjects**")
            col4.write("**Desc Summary**")
            col5.write("**Physical Desc**")
            col6.write("**MSRP**")

            # Rows
            row_color = False
            for book in books:
                row_bg = "#f9f9f9" if row_color else "white"
                st.markdown(
                    f'<div style="background-color:{row_bg}; padding:5px; margin:2px 0; border-radius:3px;">',
                    unsafe_allow_html=True,
                )
                col1, col2, col3, col4, col5, col6 = st.columns([1, 3, 2, 2, 2, 2])
                col1.write(str(book.volume_number))

                # Cover and title
                cover_url = fetch_cover_for_book(book)
                with col2:
                    if cover_url:
                        st.image(cover_url, width=60)
                    st.write(book.book_title or "N/A")

                col3.write(", ".join(book.genres) if book.genres else "N/A")
                desc = book.description or "N/A"
                col4.write(desc[:100] + "..." if len(desc) > 100 else desc)
                col5.write(book.physical_description or "N/A")
                col6.write(f"${book.msrp_cost:.2f}" if book.msrp_cost else "N/A")
                st.markdown("</div>", unsafe_allow_html=True)
                row_color = not row_color

            # Warnings
            warnings = [w for book in books for w in (book.warnings or [])]
            if warnings:
                st.warning("Warnings: " + "; ".join(set(warnings)))

            st.divider()

        # Export options
        st.subheader("Export Options")
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            if st.button("Export to MARC", type="primary"):
                try:
                    import os
                    import tempfile

                    with tempfile.NamedTemporaryFile(
                        mode="w+b",
                        suffix=".mrc",
                        delete=False,
                    ) as temp_file:
                        temp_path = temp_file.name
                        export_books_to_marc(st.session_state.all_books, temp_path)
                        with open(temp_path, "rb") as f:
                            marc_data = f.read()
                        os.unlink(temp_path)
                    st.download_button(
                        label="Download MARC file",
                        data=marc_data,
                        file_name="manga_collection.mrc",
                        mime="application/octet-stream",
                    )
                except Exception:
                    st.error("An error occurred during the export process.")
                except Exception:
                    st.error("An error occurred during the export process.")
        with col2:
            if st.button("Download Project State JSON"):
                try:
                    import json

                    state_data = (
                        st.session_state.project_state.__dict__
                    )  # Get the dict of ProjectState
                    json_data = json.dumps(state_data, indent=2)
                    st.download_button(
                        label="Download JSON file",
                        data=json_data,
                        file_name="project_state.json",
                        mime="application/json",
                    )
                except Exception:
                    st.error("An error occurred during the export process.")
        with col3:
            if st.button("Print Labels"):
                st.session_state.show_label_form = True
        with col4:
            # Clear results and start over
            if st.button("Start New Lookup"):
                st.session_state.all_books = []
                st.session_state.series_entries = []
                st.session_state.confirmed_series = []

        st.subheader("Print Labels")
        with st.form("label_form"):
            label_id = st.selectbox("Label Identifier", ["A", "B", "C", "D"])
            clipart = st.selectbox(
                "Clipart",
                [
                    "None",
                    "Duck",
                    "Mouse",
                    "Cat",
                    "Dog",
                    "Padlock",
                    "Chili Pepper",
                    "Eyeglasses",
                    "Handcuffs",
                ],
            )
            submitted = st.form_submit_button("Generate Labels")
            if submitted:
                # Generate label data
                from label_generator import generate_pdf_sheet

                label_data = []
                for book in st.session_state.all_books:
                    label_data.append(
                        {
                            "Title": book.book_title or book.series_name,
                            "Author's Name": (
                                ", ".join(book.authors) if book.authors else "Unknown"
                            ),
                            "Publication Year": (
                                str(book.copyright_year) if book.copyright_year else ""
                            ),
                            "Series Title": book.series_name,
                            "Series Volume": str(book.volume_number),
                            "Call Number": f"Manga {book.barcode}",
                            "Holdings Barcode": book.barcode,
                            "spine_label_id": label_id,
                            "clipart": clipart,
                        },
                    )
                pdf_data = generate_pdf_sheet(label_data)
                st.download_button(
                    label="Download Labels PDF",
                    data=pdf_data,
                    file_name="manga_labels.pdf",
                    mime="application/pdf",
                )
                st.session_state.show_label_form = False
        if st.button("Cancel"):
            st.session_state.show_label_form = False

    else:
        # Show series input form
        series_input_form()


if __name__ == "__main__":
    main()
# Trivial update to trigger redeploy
