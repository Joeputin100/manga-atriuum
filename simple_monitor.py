#!/usr/bin/env python3
"""
Simple Progress Monitor

Displays progress of manga database operations.
"""

import os
import time
import json

def get_log_progress(log_file):
    """Parse progress from a log file"""
    if not os.path.exists(log_file):
        return {"volumes_added": 0, "current_series": "Not started", "status": "Idle"}

    try:
        with open(log_file, 'r') as f:
            lines = f.readlines()

        volumes_added = sum(1 for line in lines if "✓ Added" in line)
        current_series = ""

        for line in reversed(lines[-20:]):
            if "🎯 Adding" in line:
                current_series = line.split("🎯 Adding ")[1].split(" (")[0]
                break

        status = "Running" if volumes_added > 0 else "Idle"
        return {"volumes_added": volumes_added, "current_series": current_series, "status": status}

    except Exception as e:
        return {"volumes_added": 0, "current_series": f"Error: {e}", "status": "Error"}

def get_database_stats():
    """Get current database statistics"""
    try:
        with open('project_state.json', 'r') as f:
            state = json.load(f)

        volumes = sum(1 for call in state.get('api_calls', []) if call.get('success'))
        return {"total_volumes": volumes}

    except:
        return {"total_volumes": 0}

def main():
    """Simple monitoring loop"""
    print("📊 Manga Database Progress Monitor")
    print("Press Ctrl+C to stop")
    print("=" * 50)

    try:
        while True:
            # Clear screen
            os.system('clear' if os.name == 'posix' else 'cls')

            # Get stats
            db_stats = get_database_stats()

            logs = {
                "Missing Volumes": "add_all_volumes_final.txt",
                "New Shonen Series": "add_new_series_log.txt",
                "Additional Series": "add_additional_series_log.txt",
                "More Series": "add_more_series_log.txt"
            }

            print("📊 Manga Database Progress Monitor")
            print(f"📚 Total Volumes in Database: {db_stats['total_volumes']}")
            print()

            total_added = 0
            active_ops = 0

            for op_name, log_file in logs.items():
                progress = get_log_progress(log_file)
                total_added += progress["volumes_added"]
                if progress["status"] == "Running":
                    active_ops += 1

                print(f"{op_name}:")
                print(f"  Status: {progress['status']}")
                print(f"  Volumes Added: {progress['volumes_added']}")
                print(f"  Current Series: {progress['current_series']}")
                print()

            print(f"📈 Session Total: {total_added} volumes added")
            print(f"⚡ Active Operations: {active_ops}")
            print()
            print("Refreshing in 10 seconds... (Ctrl+C to stop)")

            time.sleep(10)

    except KeyboardInterrupt:
        print("\nMonitoring stopped. Your manga database is growing! 📚")

if __name__ == "__main__":
    main()