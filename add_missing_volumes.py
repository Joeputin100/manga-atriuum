#!/usr/bin/env python3
"""
Add Missing Volumes for All Series

This script identifies missing volumes for all series in the database
and fetches their data using the DeepSeek API.
"""

import os
import json
import time
from collections import defaultdict
from typing import List, Dict, Set

# Import existing modules
from manga_lookup import DeepSeekAPI, DataValidator, GoogleBooksAPI, process_book_data, ProjectState

def get_current_volumes() -> Dict[str, Set[int]]:
    """Get current volumes per series from project_state.json"""
    try:
        with open('project_state.json', 'r') as f:
            state = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}

    series_volumes = defaultdict(set)

    for api_call in state.get('api_calls', []):
        if api_call.get('success', False):
            try:

                                print(f"    Failed after {max_retries} attempts: {e}")

                                book_data = None

                        else:

                            print(f"    Non-network error: {e}")

                            book_data = None

                            break
                book_data = deepseek_api.get_book_info(series, volume, project_state)

                if book_data:
                    # Process the data
                    book = process_book_data(book_data, volume, google_api, project_state)

                    if book:
                        print(f"    ✓ Added {series} Vol. {volume}")
                        added_count += 1
                    else:
                        print(f"    ✗ Failed to process {series} Vol. {volume}")
                else:
                    print(f"    ✗ Failed to fetch {series} Vol. {volume}")

            except Exception as e:
                print(f"    ✗ Error processing {series} Vol. {volume}: {e}")

            # Rate limiting
            time.sleep(2)

    print(f"\n🎉 Completed! Added {added_count} missing volumes")

if __name__ == "__main__":
    main()