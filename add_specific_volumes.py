#!/usr/bin/env python3
"""
Add Specific Missing Volumes

Manually add a few missing volumes for testing.
"""

from manga_lookup import DeepSeekAPI, GoogleBooksAPI, process_book_data, ProjectState

def main():
    # Initialize
    project_state = ProjectState()
    deepseek_api = DeepSeekAPI()
    google_api = GoogleBooksAPI()

    # Volumes to add
    volumes_to_add = [
        ("One Piece", 11),
        ("One Piece", 12),
        ("One Piece", 13),
        ("Death Note", 6),
        ("Death Note", 7),
        ("Death Note", 8),
    ]

    added_count = 0

    for series, volume in volumes_to_add:
        print(f"Adding {series} Volume {volume}...")

        try:
            # Get book info
            book_data = deepseek_api.get_book_info(series, volume, project_state)

            if book_data:
                # Process the data
                book = process_book_data(book_data, volume, google_api, project_state)

                if book:
                    print(f"✓ Successfully added {series} Vol. {volume}")
                    added_count += 1
                else:
                    print(f"✗ Failed to process {series} Vol. {volume}")
            else:
                print(f"✗ Failed to fetch data for {series} Vol. {volume}")

        except Exception as e:
            print(f"✗ Error: {e}")

        # Rate limiting
        import time
        time.sleep(2)

    print(f"\nCompleted! Added {added_count} volumes")

if __name__ == "__main__":
    main()