#!/usr/bin/env python3
"""
Test script for manga_lookup functionality
"""

import sys
import os

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(__file__))

from manga_lookup import BookDataFetcher

def test_title_formatting():
    """Test the title formatting functionality"""
    fetcher = BookDataFetcher()

    test_cases = [
        ("The Last of the Mohicans", "Last of the Mohicans, The"),
        ("A Tale of Two Cities", "Tale of Two Cities, A"),
        ("An American Tragedy", "American Tragedy, An"),
        ("One Piece", "One Piece"),
        ("Naruto", "Naruto"),
        ("", ""),
    ]

    print("Testing title formatting:")
    for input_title, expected_output in test_cases:
        result = fetcher.format_title(input_title)
        status = "✓" if result == expected_output else "✗"
        print(f"  {status} '{input_title}' -> '{result}' (expected: '{expected_output}')")

def test_project_state():
    """Test project state functionality"""
    from manga_lookup import ProjectState

    # Create a temporary state file
    state = ProjectState("test_state.json")

    # Test initial state
    assert state.state["interaction_count"] == 0
    assert state.state["searches"] == []

    # Test recording interaction
    state.record_interaction("One Piece volumes 1-3", 3)
    assert state.state["interaction_count"] == 1
    assert state.state["total_books_found"] == 3
    assert len(state.state["searches"]) == 1

    # Clean up
    if os.path.exists("test_state.json"):
        os.remove("test_state.json")

    print("✓ Project state tests passed")

if __name__ == "__main__":
    print("Running manga lookup tests...\n")
    test_title_formatting()
    print()
    test_project_state()
    print("\nAll tests completed!")