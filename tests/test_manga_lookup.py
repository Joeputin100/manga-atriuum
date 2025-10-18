#!/usr/bin/env python3
"""
Test script for manga_lookup functionality
"""

import os
import sqlite3
from unittest.mock import MagicMock, patch

import pytest

from manga_lookup import (
    DataValidator,
    DeepSeekAPI,
    GoogleBooksAPI,
    ProjectState,
    parse_volume_range,
    generate_sequential_barcodes,
    process_book_data,
    BookInfo,
)


@pytest.fixture
def project_state():
    """Fixture for a temporary ProjectState instance"""
    db_file = "test_project_state.db"
    state = ProjectState(db_file=db_file)
    yield state
    state.conn.close()
    os.remove(db_file)


def test_title_formatting():
    """Test the title formatting functionality"""
    test_cases = [
        ("The Last of the Mohicans", "Last of the Mohicans, The"),
        ("A Tale of Two Cities", "Tale of Two Cities, A"),
        ("An American Tragedy", "American Tragedy, An"),
        ("One Piece", "One Piece"),
        ("Naruto", "Naruto"),
        ("", ""),
    ]

    for input_title, expected_output in test_cases:
        result = DataValidator.format_title(input_title)
        assert result == expected_output


def test_project_state(project_state):
    """Test project state functionality"""
    # Test initial state
    assert project_state._get_metadata("interaction_count") == "0"
    cursor = project_state.conn.cursor()
    cursor.execute("SELECT * FROM searches")
    assert len(cursor.fetchall()) == 0

    # Test recording interaction
    project_state.record_interaction("One Piece volumes 1-3", 3)
    assert project_state._get_metadata("interaction_count") == "1"
    assert project_state._get_metadata("total_books_found") == "3"
    cursor.execute("SELECT * FROM searches")
    assert len(cursor.fetchall()) == 1


@patch("requests.post")
def test_deepseek_api_correct_series_name(mock_post):
    """Test the correct_series_name method of the DeepSeekAPI class"""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "choices": [
            {
                "message": {
                    "content": '["One Piece", "One Piece (Omnibus Edition)"]'
                }
            }
        ]
    }
    mock_post.return_value = mock_response

    deepseek_api = DeepSeekAPI()
    suggestions = deepseek_api.correct_series_name("One Piece")
    assert suggestions == ["One Piece", "One Piece (Omnibus Edition)"]


@patch("requests.get")
def test_google_books_api_get_cover_image_url(mock_get):
    """Test the get_cover_image_url method of the GoogleBooksAPI class"""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "totalItems": 1,
        "items": [
            {
                "volumeInfo": {
                    "imageLinks": {
                        "smallThumbnail": "http://example.com/cover.jpg"
                    }
                }
            }
        ],
    }
    mock_get.return_value = mock_response

    google_books_api = GoogleBooksAPI()
    cover_url = google_books_api.get_cover_image_url("1234567890")
    assert cover_url == "http://example.com/cover.jpg"


def test_parse_volume_range():
    """Test the parse_volume_range function"""
    assert parse_volume_range("1-5,7,10") == [1, 2, 3, 4, 5, 7, 10]
    assert parse_volume_range("17-18-19") == [17, 18, 19]
    with pytest.raises(ValueError):
        parse_volume_range("1-a")


def test_generate_sequential_barcodes():
    """Test the generate_sequential_barcodes function"""
    assert generate_sequential_barcodes("T000001", 3) == ["T000001", "T000002", "T000003"]
    with pytest.raises(ValueError):
        generate_sequential_barcodes("invalid", 3)

def test_process_book_data():
    """Test the process_book_data function"""
    raw_data = {
        "series_name": "One Piece",
        "book_title": "One Piece, Vol. 1",
        "authors": ["Eiichiro Oda"],
        "msrp_cost": "9.99",
        "isbn_13": "978-1421506623",
        "publisher_name": "VIZ Media LLC",
        "copyright_year": "2003",
        "description": "As a child, Monkey D. Luffy was inspired to become a pirate by listening to the tales of the buccaneer \"Red-Haired\" Shanks.",
        "physical_description": "216 pages : illustrations ; 19 cm",
        "genres": ["Action", "Adventure", "Comedy", "Fantasy"],
    }
    book_info = process_book_data(raw_data, 1)
    assert isinstance(book_info, BookInfo)
    assert book_info.series_name == "One Piece"
    assert book_info.volume_number == 1
    assert book_info.msrp_cost == 9.99
