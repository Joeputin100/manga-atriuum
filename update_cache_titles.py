#!/usr/bin/env python3
"""
Update Cache Titles

Update all cached entries to ensure book titles include the series name as a substring.
If the book title doesn't include the series title, add it to the beginning with a colon.
"""

import sys
import os
import json
import re
from typing import Dict, List

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(__file__))

from manga_lookup import ProjectState


def extract_series_name_from_prompt(prompt: str) -> str:
    """Extract series name from DeepSeek API prompt"""
    # Look for pattern: "manga series \"series_name\""
    match = re.search(r'manga series["\']?([^"\']+)["\']?', prompt, re.IGNORECASE)
    if match:
        return match.group(1).strip()

    # Fallback: look for series name after "manga series"
    match = re.search(r'manga series\s+([^\n"]+)', prompt, re.IGNORECASE)
    if match:
        return match.group(1).strip()

    return ""


def update_book_title_with_series(book_data: Dict, series_name: str) -> Dict:
    """Update book title to include series name if not present"""
    if not book_data or not isinstance(book_data, dict):
        return book_data

    if 'book_title' not in book_data:
        return book_data

    current_title = book_data['book_title']

    # Check if series name is already in the title (case-insensitive)
    if series_name.lower() in current_title.lower():
        return book_data  # No changes needed

    # Add series name to the beginning with a colon
    new_title = f"{series_name}: {current_title}"
    book_data['book_title'] = new_title

    return book_data


def main():
    """Main function to update all cached entries"""
    print("🔄 Updating Cache Titles")
    print("=" * 60)
    print("Ensuring all book titles include the series name...")

    # Load project state
    project_state = ProjectState()

    updated_count = 0
    total_cached = len(project_state.state['cached_responses'])

    print(f"\nProcessing {total_cached} cached responses...")

    for cache_key, cached_response in list(project_state.state['cached_responses'].items()):
        try:
            # Parse the JSON response
            book_data = json.loads(cached_response)

            # Extract series name from cache key or prompt
            series_name = ""

            # Try to find the series name in the cache key
            if '_' in cache_key:
                # Look for series name in cache key
                parts = cache_key.split('_')
                # The prompt part contains the series name
                prompt_part = ' '.join(parts[:-1])
                series_name = extract_series_name_from_prompt(prompt_part)

            # If we couldn't extract series name, skip this entry
            if not series_name:
                continue

            # Update the book title if needed
            original_title = book_data.get('book_title', '')
            updated_book_data = update_book_title_with_series(book_data, series_name)

            # If title was updated, save the changes
            if updated_book_data.get('book_title') != original_title:
                updated_response = json.dumps(updated_book_data)
                project_state.state['cached_responses'][cache_key] = updated_response
                updated_count += 1
                print(f"  ✓ Updated: {original_title} → {updated_book_data['book_title']}")

        except Exception as e:
            print(f"  ✗ Error processing cache entry {cache_key}: {e}")
            continue

    # Save the updated state
    if updated_count > 0:
        project_state.save_state()
        print(f"\n💾 Updated {updated_count} out of {total_cached} cached entries")
        print(f"📁 Project state saved to {project_state.state_file}")
    else:
        print(f"\n✅ No updates needed. All {total_cached} entries are already correct.")

    print("\n✅ Cache title update completed!")


if __name__ == "__main__":
    main()