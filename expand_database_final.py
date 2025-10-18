#!/usr/bin/env python3
"""
Expand Database with All Extant Volumes

Adds all extant volumes for existing series (missing ones) and 10 new popular shonen series.
Commits and pushes after every 10 volumes.
"""

import json
import subprocess
import time
from collections import defaultdict

# Import existing modules
from manga_lookup import DeepSeekAPI, GoogleBooksAPI, ProjectState, process_book_data


def get_current_volumes() -> dict:
    """Get current volumes per series from project_state.json"""
    try:
        with open("project_state.json") as f:
            state = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}

    series_volumes = defaultdict(set)

    for api_call in state.get("api_calls", []):
        if api_call.get("success", False):
            try:
                response = json.loads(api_call["response"])
                series = response.get("series_name")
                volume = api_call.get("volume")
                if series and volume:
                    series_volumes[series].add(volume)
            except json.JSONDecodeError:
                continue

    return dict(series_volumes)

def find_missing_volumes(series_volumes: dict, max_volumes: dict) -> dict:
    """Find missing volumes for each series"""
    missing = {}

    for series, current_vols in series_volumes.items():
        if series in max_volumes:
            max_vol = max_volumes[series]
            current_max = max(current_vols) if current_vols else 0

            # For long-running series, be conservative with max_vol
            if max_vol > 50 and current_max < max_vol * 0.8:
                # Assume we have most volumes up to current_max + some buffer
                assumed_max = min(max_vol, current_max + 20)
            else:
                assumed_max = max_vol

            missing_vols = []
            for vol in range(1, assumed_max + 1):
                if vol not in current_vols:
                    missing_vols.append(vol)

            if missing_vols:
                missing[series] = missing_vols

    # Also add new series (not in current_volumes)
    for series, max_vol in max_volumes.items():
        if series not in series_volumes:
            missing[series] = list(range(1, max_vol + 1))

    return missing

def get_book_data_with_retry(api, series, volume, project_state, max_retries=3):
    """Get book data with retry logic for network errors"""
    for attempt in range(max_retries):
        try:
            return api.get_book_info(series, volume, project_state)
        except Exception as e:
            if ("SSL" in str(e) or "Max retries exceeded" in str(e)) and attempt < max_retries - 1:
                print(f"    Network error, retrying in 5 seconds... (attempt {attempt + 1}/{max_retries})")
                time.sleep(5)
            else:
                print(f"    Failed after {max_retries} attempts: {e}")
                return None
    return None

def commit_and_push(count):
    """Commit and push changes after every 10 volumes"""
    try:
        subprocess.run(["git", "add", "project_state.json"], check=True)
        subprocess.run(["git", "commit", "-m", f"feat: add {count} volumes to database"], check=True)
        subprocess.run(["git", "push", "origin", "main"], check=True)
        print(f"✓ Committed and pushed after {count} volumes")
    except subprocess.CalledProcessError as e:
        print(f"✗ Git operation failed: {e}")

def main():
    """Expand database with all extant volumes"""
    print("🚀 Expanding Database with All Extant Volumes")
    print("=" * 60)

    # All series with their max volumes (existing partial + new)
    max_volumes = {
        "One Piece": 110,
        "Naruto": 72,
        "Bleach": 74,
        "Death Note": 13,
        "Attack on Titan": 34,
        "Attack on Titan: Before the Fall": 17,
        "Black Butler": 32,
        "Black Clover": 33,
        "Blue Exorcist": 27,
        "Boruto: Naruto Next Generations": 18,
        "Boruto: Naruto The Next Generation": 18,
        "Boruto: Two Blue Vortex": 5,
        "Cells At Work": 8,
        "Deadman Wonderland": 13,
        "Golden Kamuy": 31,
        "Haikyuu!!": 45,
        "Mob Psycho 100": 16,
        "Noragami: Stray God": 27,
        "One Punch Man": 26,
        "Silent Voice, A": 7,
        "To Your Eternity": 18,
        "Tokyo Ghoul": 14,
        "Tokyo Ghoul:re": 16,
        "Akira": 6,
        "Assassination Classroom": 21,
        "Barefoot Gen: A Cartoon Story of Hiroshima": 10,
        "Show-ha Shoten": 6,
        "Show-ha Shoten!": 6,
        "Demon Slayer: Kimetsu no Yaiba": 23,
        "Jujutsu Kaisen": 23,
        "My Hero Academia": 38,
        "Chainsaw Man": 15,
        "Spy x Family": 11,
        "Dr. Stone": 26,
        "Fire Force": 34,
        "The Rising of the Shield Hero": 45,
        "Crayon Shin-chan": 60,
        "Happiness": 50,
    }

    current_volumes = get_current_volumes()
    print(f"Found {len(current_volumes)} existing series with volumes")

    missing_volumes = find_missing_volumes(current_volumes, max_volumes)

    total_missing = sum(len(vols) for vols in missing_volumes.values())
    print(f"Found {total_missing} missing volumes across {len(missing_volumes)} series")

    if not missing_volumes:
        print("No missing volumes found!")
        return

    # Initialize APIs
    project_state = ProjectState()
    deepseek_api = DeepSeekAPI()
    google_api = GoogleBooksAPI()

    total_added = 0
    commit_count = 0

    for series, volumes in missing_volumes.items():
        print(f"\n🎯 Adding {series} - {len(volumes)} missing volumes")

        series_added = 0

        for volume in volumes:
            print(f"  Fetching {series} Volume {volume}...")

            # Get book info with retry
            book_data = get_book_data_with_retry(deepseek_api, series, volume, project_state)

            if book_data:
                # Process the data
                book = process_book_data(book_data, volume, google_api, project_state)

                if book:
                    print(f"    ✓ Added {series} Vol. {volume}")
                    series_added += 1
                    total_added += 1
                    commit_count += 1

                    # Save incrementally
                    state_dict = {
                        "api_calls": getattr(project_state, "api_calls", []),
                        "cached_responses": getattr(project_state, "cached_responses", {}),
                        "start_time": getattr(project_state, "start_time", None),
                        "interactions": getattr(project_state, "interactions", []),
                    }
                    with open("project_state.json", "w") as f:
                        json.dump(state_dict, f, indent=2)

                    # Commit and push every 10 volumes
                    if commit_count >= 10:
                        commit_and_push(total_added)
                        commit_count = 0
                else:
                    print(f"    ✗ Failed to process {series} Vol. {volume}")
            else:
                print(f"    ✗ Failed to fetch {series} Vol. {volume}")

            # Rate limiting
            time.sleep(2)

        print(f"  ✅ Completed {series}: {series_added}/{len(volumes)} volumes added")

    # Final commit if any remaining
    if commit_count > 0:
        commit_and_push(total_added)

    print(f"\n🎉 Grand Total: Added {total_added} volumes across all series!")

if __name__ == "__main__":
    main()
