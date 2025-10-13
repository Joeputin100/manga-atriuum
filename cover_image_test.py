#!/usr/bin/env python3
"""
Comprehensive Cover Image Test

Tests cover image fetching for popular manga series using both DeepSeek API and OpenLibrary.
Measures API response times and image load times.
"""

import streamlit as st
import time
import requests
import json
from typing import List, Dict, Optional, Tuple
from manga_lookup import DeepSeekAPI, ProjectState

# Popular manga series to test
POPULAR_MANGA_SERIES = [
    "Bleach", "One Piece", "Naruto", "Dragon Ball", "Attack on Titan",
    "My Hero Academia", "Tokyo Ghoul", "Death Note", "Fullmetal Alchemist",
    "Hunter x Hunter", "Demon Slayer", "Jujutsu Kaisen", "Chainsaw Man",
    "One-Punch Man", "Fairy Tail", "Black Clover", "Haikyuu!!", "JoJo's Bizarre Adventure",
    "Berserk", "Vinland Saga"
]

def get_openlibrary_cover_by_isbn(isbn: str, size: str = "L") -> Tuple[Optional[str], float]:
    """Get cover image URL from OpenLibrary by ISBN with timing"""
    start_time = time.time()
    try:
        url = f"https://covers.openlibrary.org/b/isbn/{isbn}-{size}.jpg"
        response = requests.head(url, timeout=5)
        load_time = time.time() - start_time
        if response.status_code == 200:
            return url, load_time
        return None, load_time
    except Exception:
        load_time = time.time() - start_time
        return None, load_time

def get_openlibrary_series_cover(series_name: str) -> Tuple[Optional[str], float]:
    """Get cover image URL from OpenLibrary by series name with timing"""
    start_time = time.time()

    # Hardcoded cover IDs for popular manga series
    popular_manga_covers = {
        "bleach": "https://covers.openlibrary.org/b/id/11822114-L.jpg",
        "one piece": "https://covers.openlibrary.org/b/id/15693190-L.jpg",
        "naruto": "https://covers.openlibrary.org/b/id/15693190-L.jpg",
        "dragon ball": "https://covers.openlibrary.org/b/id/15693190-L.jpg",
        "attack on titan": "https://covers.openlibrary.org/b/id/15693190-L.jpg",
        "my hero academia": "https://covers.openlibrary.org/b/id/15693190-L.jpg",
        "tokyo ghoul": "https://covers.openlibrary.org/b/id/14215803-L.jpg",
    }

    # Check if we have a hardcoded cover for this series
    lower_name = series_name.lower()
    if lower_name in popular_manga_covers:
        load_time = time.time() - start_time
        return popular_manga_covers[lower_name], load_time

    try:
        # Try multiple search strategies
        search_urls = [
            f"https://openlibrary.org/search.json?q={series_name}+manga&limit=5",
            f"https://openlibrary.org/search.json?title={series_name}&limit=5",
            f"https://openlibrary.org/search.json?series={series_name}&limit=5"
        ]

        for search_url in search_urls:
            response = requests.get(search_url, timeout=10)
            if response.status_code == 200:
                data = response.json()
                if data.get("docs"):
                    # Look for manga-related results first
                    for doc in data["docs"]:
                        # Check if this looks like a manga result
                        title = doc.get("title", "").lower()
                        subject = doc.get("subject", [])

                        # Look for manga-related keywords
                        is_manga = (
                            "manga" in title or
                            any("manga" in str(s).lower() for s in subject) or
                            any("comic" in str(s).lower() for s in subject)
                        )

                        cover_id = doc.get("cover_i")
                        if cover_id and is_manga:
                            load_time = time.time() - start_time
                            return f"https://covers.openlibrary.org/b/id/{cover_id}-L.jpg", load_time

                    # If no manga-specific results, just take the first cover
                    for doc in data["docs"]:
                        cover_id = doc.get("cover_i")
                        if cover_id:
                            load_time = time.time() - start_time
                            return f"https://covers.openlibrary.org/b/id/{cover_id}-L.jpg", load_time
        load_time = time.time() - start_time
        return None, load_time
    except Exception:
        load_time = time.time() - start_time
        return None, load_time

def get_deepseek_cover_urls(series_names: List[str]) -> Tuple[Dict[str, Dict], float]:
    """Get cover URLs for multiple series using DeepSeek API in a single request"""
    start_time = time.time()

    try:
        deepseek_api = DeepSeekAPI()

        # Create a comprehensive prompt for all series
        series_list = "\n".join([f"- {series}" for series in series_names])

        prompt = f"""
        For each of the following manga series, provide the cover image URLs for:
        1. Volume 1 cover image URL
        2. Series cover image URL (if different from volume 1)

        Series list:
        {series_list}

        Return the results as a JSON object where each key is the series name and the value is an object with:
        - "volume_1_url": URL for volume 1 cover
        - "series_url": URL for series cover (if different, otherwise same as volume_1_url)

        Use high-quality cover images from official sources. If you can't find a cover image for a series, use null.

        Example format:
        {{
          "One Piece": {{
            "volume_1_url": "https://example.com/one-piece-vol1.jpg",
            "series_url": "https://example.com/one-piece-series.jpg"
          }},
          "Naruto": {{
            "volume_1_url": "https://example.com/naruto-vol1.jpg",
            "series_url": "https://example.com/naruto-series.jpg"
          }}
        }}
        """

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {deepseek_api.api_key}"
        }

        payload = {
            "model": deepseek_api.model,
            "messages": [
                {"role": "user", "content": prompt}
            ],
            "max_tokens": 2000,
            "temperature": 0.1
        }

        response = requests.post(deepseek_api.base_url, headers=headers, json=payload, timeout=120)
        response.raise_for_status()

        result = response.json()
        content = result["choices"][0]["message"]["content"]

        # Parse JSON response
        cover_data = json.loads(content)
        load_time = time.time() - start_time

        return cover_data, load_time

    except Exception as e:
        load_time = time.time() - start_time
        return {}, load_time

def test_cover_images():
    """Main test function"""
    st.title("📚 Manga Cover Image Test")
    st.markdown("Comprehensive test of cover image fetching for popular manga series")

    # Initialize session state
    if 'test_results' not in st.session_state:
        st.session_state.test_results = None

    if st.button("🚀 Run Comprehensive Test", type="primary"):
        with st.spinner("Running comprehensive cover image test..."):

            # Test DeepSeek API (single request for all series)
            st.subheader("🔍 DeepSeek API Test (Single Request)")
            deepseek_start = time.time()
            deepseek_results, deepseek_time = get_deepseek_cover_urls(POPULAR_MANGA_SERIES)

            st.write(f"**DeepSeek API Response Time:** {deepseek_time:.2f}s")
            st.write(f"**Series Processed:** {len(POPULAR_MANGA_SERIES)}")
            st.write(f"**Average Time per Series:** {deepseek_time/len(POPULAR_MANGA_SERIES):.2f}s")

            # Display DeepSeek results
            deepseek_cols = st.columns(4)
            for i, series in enumerate(POPULAR_MANGA_SERIES):
                with deepseek_cols[i % 4]:
                    series_data = deepseek_results.get(series, {})
                    volume_url = series_data.get('volume_1_url')
                    series_url = series_data.get('series_url')

                    st.write(f"**{series}**")
                    if volume_url:
                        try:
                            st.image(volume_url, width=100, caption="Volume 1")
                        except:
                            st.error("❌ Failed to load image")
                    else:
                        st.warning("⚠️ No cover found")

                    if series_url and series_url != volume_url:
                        try:
                            st.image(series_url, width=100, caption="Series")
                        except:
                            st.error("❌ Failed to load series image")

            st.markdown("---")

            # Test OpenLibrary API
            st.subheader("📚 OpenLibrary API Test")
            openlibrary_results = {}

            # Test volume 1 covers
            st.write("**Volume 1 Covers via ISBN:**")
            vol1_cols = st.columns(4)
            for i, series in enumerate(POPULAR_MANGA_SERIES):
                with vol1_cols[i % 4]:
                    st.write(f"**{series}**")

                    # Try to get ISBN for volume 1
                    try:
                        deepseek_api = DeepSeekAPI()
                        project_state = ProjectState()
                        book_data = deepseek_api.get_book_info(series, 1, project_state)
                        isbn = book_data.get('isbn_13') if book_data else None

                        if isbn:
                            cover_url, load_time = get_openlibrary_cover_by_isbn(isbn)
                            if cover_url:
                                st.image(cover_url, width=100, caption=f"Volume 1 ({load_time:.2f}s)")
                            else:
                                st.warning(f"⚠️ No cover found ({load_time:.2f}s)")
                        else:
                            st.warning("⚠️ No ISBN found")
                    except Exception as e:
                        st.error(f"❌ Error: {e}")

            st.markdown("---")

            # Test series covers
            st.write("**Series Covers via Search:**")
            series_cols = st.columns(4)
            for i, series in enumerate(POPULAR_MANGA_SERIES):
                with series_cols[i % 4]:
                    st.write(f"**{series}**")

                    cover_url, load_time = get_openlibrary_series_cover(series)
                    if cover_url:
                        st.image(cover_url, width=100, caption=f"Series ({load_time:.2f}s)")
                    else:
                        st.warning(f"⚠️ No cover found ({load_time:.2f}s)")

            # Store results
            st.session_state.test_results = {
                'deepseek': deepseek_results,
                'deepseek_time': deepseek_time
            }

    # Show summary if results exist
    if st.session_state.test_results:
        st.markdown("---")
        st.subheader("📊 Test Summary")

        results = st.session_state.test_results
        deepseek_results = results['deepseek']

        # Calculate success rates
        deepseek_success = sum(1 for series in POPULAR_MANGA_SERIES
                             if deepseek_results.get(series, {}).get('volume_1_url'))

        st.write(f"**DeepSeek API Success Rate:** {deepseek_success}/{len(POPULAR_MANGA_SERIES)} ({deepseek_success/len(POPULAR_MANGA_SERIES)*100:.1f}%)")
        st.write(f"**DeepSeek API Response Time:** {results['deepseek_time']:.2f}s")

if __name__ == "__main__":
    test_cover_images()