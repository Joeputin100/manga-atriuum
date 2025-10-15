#!/usr/bin/env python3
"""
Enhanced Progress Monitor

Displays progress of manga database operations with detailed metrics.
"""

import os
import time
import json

def get_log_progress(log_file):
    """Parse progress from a log file"""
    if not os.path.exists(log_file):
        return {"volumes_added": 0, "current_series": "Not started", "status": "Idle", "total_expected": 0, "remaining": 0}

    try:
        with open(log_file, 'r') as f:
            lines = f.readlines()

        volumes_added = sum(1 for line in lines if "✓ Added" in line)
        current_series = ""
        total_expected = 0

        # Get total expected from log
        for line in lines:
            if "Found" in line and "missing volumes across" in line:
                parts = line.split()
                try:
                    total_expected = int(parts[1])
                except:
                    pass
                break
            elif "volumes:" in line and "🎯 Adding" in line:
                # For series addition logs
                parts = line.split(" (")
                if len(parts) > 1:
                    vol_part = parts[1].split("-")[1].split(" ")[0]
                    try:
                        total_expected = int(vol_part)
                    except:
                        pass

        for line in reversed(lines[-20:]):
            if "🎯 Adding" in line:
                current_series = line.split("🎯 Adding ")[1].split(" (")[0]
                break

        status = "Running" if volumes_added > 0 else "Idle"
        remaining = max(0, total_expected - volumes_added) if total_expected > 0 else 0

        return {
            "volumes_added": volumes_added,
            "current_series": current_series,
            "status": status,
            "total_expected": total_expected,
            "remaining": remaining
        }

    except Exception as e:
        return {"volumes_added": 0, "current_series": f"Error: {e}", "status": "Error", "total_expected": 0, "remaining": 0}

def get_database_stats():
    """Get current database statistics"""
    try:
        with open('project_state.json', 'r') as f:
            state = json.load(f)

        volumes = sum(1 for call in state.get('api_calls', []) if call.get('success'))
        return {"total_volumes": volumes}

    except:
        return {"total_volumes": 0}

def get_file_sizes():
    """Get sizes of database files"""
    sizes = {}
    files = ["project_state.json", "project_state.db"]
    for file in files:
        if os.path.exists(file):
            size = os.path.getsize(file)
            sizes[file] = f"{size / (1024*1024):.1f} MB"
        else:
            sizes[file] = "Not found"
    return sizes

def main():
    """Enhanced monitoring loop"""
    start_time = time.time()
    operations_start = {}

    try:
        while True:
            # Clear screen
            os.system('clear' if os.name == 'posix' else 'cls')

            # Get stats
            current_time = time.time()
            elapsed = current_time - start_time
            db_stats = get_database_stats()
            file_sizes = get_file_sizes()

            logs = {
                "Missing Volumes": "add_all_volumes_final.txt",
                "New Shonen Series": "add_new_series_log.txt",
                "Additional Series": "add_additional_series_log.txt",
                "More Series": "add_more_series_log.txt"
            }

            print("📊 Enhanced Manga Database Progress Monitor")
            print(f"📚 Total Volumes in Database: {db_stats['total_volumes']}")
            print(f"⏱️  Session Time: {elapsed:.0f} seconds")
            print()

            total_added = 0
            active_ops = 0
            total_api_rate = 0
            total_download_rate = 0
            active_count = 0

            for op_name, log_file in logs.items():
                progress = get_log_progress(log_file)
                total_added += progress["volumes_added"]
                if progress["status"] == "Running":
                    active_ops += 1
                    if op_name not in operations_start:
                        operations_start[op_name] = current_time
                    op_elapsed = current_time - operations_start[op_name]
                    if op_elapsed > 0 and progress["volumes_added"] > 0:
                        rate = progress["volumes_added"] / op_elapsed
                        total_api_rate += rate
                        total_download_rate += rate  # Assuming 1:1 for simplicity
                        active_count += 1

                print(f"{op_name}:")
                print(f"  Status: {progress['status']}")
                print(f"  Volumes Added: {progress['volumes_added']}")
                if progress.get('total_expected', 0) > 0:
                    print(f"  Remaining: {progress.get('remaining', 0)}")
                print(f"  Current Series: {progress['current_series']}")
                print()

            print(f"📈 Session Total: {total_added} volumes added")
            print(f"⚡ Active Operations: {active_ops}")

            if active_count > 0:
                avg_api_rate = total_api_rate / active_count
                avg_download_rate = total_download_rate / active_count
                print(f"🔄 Avg API Calls/Second: {avg_api_rate:.3f}")
                print(f"📥 Avg Downloads/Second: {avg_download_rate:.3f}")

            print(f"💾 JSON DB Size: {file_sizes.get('project_state.json', 'N/A')}")
            print(f"💾 SQLite DB Size: {file_sizes.get('project_state.db', 'N/A')}")
            print()
            print("Refreshing in 10 seconds... (Ctrl+C to stop)")

            time.sleep(10)

    except KeyboardInterrupt:
        print("\nMonitoring stopped. Your manga database is growing! 📚")

if __name__ == "__main__":
    main()