#!/usr/bin/env python3
"""
Cache Series Names for Correction Workflow

Precache series name suggestions for the most popular manga series
so the correction workflow shows results very quickly.
"""

import sys
import os
import time
from typing import List

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(__file__))

from manga_lookup import DeepSeekAPI, ProjectState


# Popular manga series to cache for correction workflow
POPULAR_SERIES = [
    "Naruto",
    "Boruto: Two Blue Vortex",
    "Boruto: Naruto The Next Generation",
    "Bleach",
    "One Piece",
    "Black Clover",
    "Tokyo Ghoul",
    "Tokyo Ghoul:re",
    "Assassination Classroom",
    "Akira",
    "My Hero Academia",
    "Fairy Tail",
    "Attack on Titan",
    "Tegami Bachi",
    "Magus of the Library",
    "Chainsaw Man",
    "Dragon Ball Z",
    # Additional popular series for better coverage
    "Jujutsu Kaisen",
    "Demon Slayer",
    "Haikyuu!!",
    "Death Note",
    "Fullmetal Alchemist",
    "Hunter x Hunter",
    "JoJo's Bizarre Adventure",
    "One Punch Man",
    "Dr. Stone",
    "The Promised Neverland",
    "Vinland Saga",
    "Berserk",
    "Vagabond",
    "Kingdom",
    "Slam Dunk",
    "Dragon Ball",
    "Dragon Ball Super",
    "Yu Yu Hakusho",
    "Rurouni Kenshin",
    "Inuyasha",
    "Sailor Moon"
]


def cache_series_corrections(series_names: List[str], project_state: ProjectState, deepseek_api: DeepSeekAPI):
    """Cache series name corrections for a list of series"""
    print(f"\n🔍 Caching series name corrections for {len(series_names)} series...")

    successful = 0
    failed = 0

    for series_name in series_names:
        try:
            print(f"  {series_name}...", end=" ")

            # Get corrected series names
            suggestions = deepseek_api.correct_series_name(series_name)

            if suggestions and len(suggestions) > 0:
                print("✓")
                successful += 1
            else:
                print("✗ (no suggestions)")
                failed += 1

            # Add small delay to respect rate limits
            time.sleep(0.5)

        except Exception as e:
            print(f"✗ (error: {str(e)[:50]})")
            failed += 1
            continue

    return successful, failed


def main():
    """Main function to cache series name corrections"""
    print("🚀 Caching Series Names for Correction Workflow")
    print("=" * 60)
    print("This will make series name suggestions appear instantly for popular series")

    # Initialize APIs
    try:
        deepseek_api = DeepSeekAPI()
        project_state = ProjectState()
    except Exception as e:
        print(f"❌ Failed to initialize APIs: {e}")
        return

    print(f"\nCaching corrections for {len(POPULAR_SERIES)} popular manga series...")
    print("=" * 60)

    # Cache series corrections
    successful, failed = cache_series_corrections(POPULAR_SERIES, project_state, deepseek_api)

    # Print summary
    print("\n" + "=" * 60)
    print("📊 Series Name Caching Summary")
    print("=" * 60)
    print(f"Series processed: {len(POPULAR_SERIES)}")
    print(f"Successfully cached: {successful}")
    print(f"Failed: {failed}")
    print(f"Total API calls made: {len(project_state.state['api_calls'])}")

    # Save final state
    project_state.save_state()
    print(f"\n💾 Project state saved to {project_state.state_file}")

    print("\n✅ Series name caching completed!")
    print("\nBenefits:")
    print("• Popular series names will show instant suggestions")
    print("• Users get faster response times for common searches")
    print("• Reduced API calls for frequently requested series")


if __name__ == "__main__":
    main()