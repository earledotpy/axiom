from __future__ import annotations

import sys
import zipfile
from datetime import datetime
from pathlib import Path

# Resolve C:\axiom dynamically if placed in C:\axiom\tools
try:
    ROOT = Path(__file__).resolve().parents[1]
except NameError:
    ROOT = Path(r"C:\axiom")


def main() -> int:
    logs_dir = ROOT / "logs"
    archive_dir = logs_dir / "archive"

    # Create archive folder if missing
    archive_dir.mkdir(parents=True, exist_ok=True)

    if not logs_dir.exists() or not logs_dir.is_dir():
        print(f"Directory not found: {logs_dir}", file=sys.stderr)
        return 1

    # Get all files directly inside logs, excluding anything already in archive
    log_files = [f for f in logs_dir.iterdir() if f.is_file()]

    if not log_files:
        print(f"No log files found in {logs_dir}")
        return 0

    # Sort files by LastWriteTime descending
    log_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)

    keep_names: set[str] = set()

    # Find newest handoff bundle manifest, if present
    manifest_files = [
        f for f in log_files
        if f.name.startswith("handoff_bundle_manifest_") and f.name.endswith(".json")
    ]

    if manifest_files:
        newest_bundle = manifest_files[0]
        
        # Extract timestamp from: handoff_bundle_manifest_2026-05-17T18-17-57Z.json
        timestamp = newest_bundle.name.replace("handoff_bundle_manifest_", "").replace(".json", "")
        print(f"Newest bundle timestamp detected: {timestamp}")

        # Keep all files from that same generated bundle timestamp
        bundle_patterns = [
            f"project_state_snapshot_{timestamp}.json",
            f"operator_command_index_{timestamp}.json",
            f"operator_command_index_{timestamp}.md",
            f"axiom_handoff_{timestamp}.md",
            f"handoff_bundle_manifest_{timestamp}.json",
        ]

        for pattern in bundle_patterns:
            target_file = logs_dir / pattern
            if target_file.is_file():
                keep_names.add(target_file.name)
    else:
        print("No handoff bundle manifest found. Keeping newest 25 files only.")

    # Safety buffer: keep newest 25 files regardless
    newest_safety_files = log_files[:25]
    for f in newest_safety_files:
        keep_names.add(f.name)

    # Separate files to keep vs. files to archive
    files_to_archive = [f for f in log_files if f.name not in keep_names]
    kept_count = len(log_files) - len(files_to_archive)
    archived_count = 0

    # Zip the old files if there are any to archive
    if files_to_archive:
        now_str = datetime.now().strftime("%Y%m%d_%H%M%S")
        zip_filename = archive_dir / f"logs_archive_{now_str}.zip"

        with zipfile.ZipFile(zip_filename, "w", zipfile.ZIP_DEFLATED) as zipf:
            for f in files_to_archive:
                # Add file to the zip archive
                zipf.write(f, arcname=f.name)
                # Delete the original file
                f.unlink()
                archived_count += 1
                
        print(f"\nCreated archive zip: {zip_filename.name}")

    print("\nAXIOM log archive complete")
    print("==========================")
    print(f"Kept in logs: {kept_count}")
    print(f"Zipped to archive: {archived_count}")
    print(f"Archive folder: {archive_dir}\n")

    print("Current files kept in logs:")
    
    # Refresh the list of kept files and sort them for the final output table
    current_logs = [f for f in logs_dir.iterdir() if f.is_file()]
    current_logs.sort(key=lambda x: x.stat().st_mtime, reverse=True)

    print(f"{'Name'.ljust(60)} LastWriteTime")
    print("-" * 85)
    for f in current_logs:
        mtime_dt = datetime.fromtimestamp(f.stat().st_mtime)
        mtime_str = mtime_dt.strftime("%Y-%m-%d %I:%M:%S %p")
        print(f"{f.name.ljust(60)} {mtime_str}")

    return 0


if __name__ == "__main__":
    sys.exit(main())