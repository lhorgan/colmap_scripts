# Written by ChatGPT

#!/usr/bin/env python3
"""
Move images listed in a text file from one directory to another.

Usage:
  python move_images.py SRC_DIR LIST_FILE DEST_DIR [--overwrite] [--dry-run] [--strict]

- SRC_DIR:   Directory containing the images.
- LIST_FILE: Text file with one image filename per line. Blank lines and lines
             starting with '#' are ignored.
- DEST_DIR:  Directory to move images into (created if it doesn't exist).
- --overwrite: Replace files in DEST_DIR if they already exist (default: skip).
- --dry-run:   Show what would be moved without making changes.
- --strict:    Exit with a non-zero status if any listed files are missing.
"""

from __future__ import annotations

from pathlib import Path
import argparse
import shutil
import sys

def read_names(list_file: Path) -> list[str]:
    with list_file.open("r", encoding="utf-8") as f:
        lines = [line.strip() for line in f]
    # drop blanks and comments
    return [ln for ln in lines if ln and not ln.lstrip().startswith("#")]

def move_images(src_dir: Path, names: list[str], dest_dir: Path, overwrite: bool, dry_run: bool) -> tuple[int, int, int]:
    moved = 0
    missing = 0
    skipped_exists = 0

    if not dest_dir.exists():
        if dry_run:
            print(f"[dry-run] Would create directory: {dest_dir}")
        else:
            dest_dir.mkdir(parents=True, exist_ok=True)

    for name in names:
        src_path = src_dir / name
        if not src_path.exists():
            print(f"[missing] {src_path}")
            missing += 1
            continue

        dest_path = dest_dir / src_path.name

        if dest_path.exists() and not overwrite:
            print(f"[skip exists] {dest_path}")
            skipped_exists += 1
            continue

        if dry_run:
            action = "Would overwrite" if dest_path.exists() else "Would move"
            print(f"[dry-run] {action}: {src_path} -> {dest_path}")
        else:
            # If overwriting, remove existing file first for cross-platform behavior
            if dest_path.exists() and overwrite:
                if dest_path.is_file() or dest_path.is_symlink():
                    dest_path.unlink()
                else:
                    # If somehow a directory with same name exists, raise
                    raise IsADirectoryError(f"Destination path is a directory: {dest_path}")
            shutil.move(str(src_path), str(dest_path))
            print(f"[moved] {src_path} -> {dest_path}")
            moved += 1

    return moved, missing, skipped_exists

def main():
    parser = argparse.ArgumentParser(description="Move images listed in a text file from one directory to another.")
    parser.add_argument("src_dir", type=Path, help="Directory containing the images.")
    parser.add_argument("list_file", type=Path, help="Path to text file with image filenames (one per line).")
    parser.add_argument("dest_dir", type=Path, help="Directory to move images into.")
    parser.add_argument("--overwrite", action="store_true", help="Overwrite files in destination if they exist.")
    parser.add_argument("--dry-run", action="store_true", help="Show actions without making changes.")
    parser.add_argument("--strict", action="store_true", help="Exit non-zero if any listed files are missing.")
    args = parser.parse_args()

    # Basic validations
    if not args.src_dir.is_dir():
        print(f"Error: source directory not found: {args.src_dir}", file=sys.stderr)
        sys.exit(2)
    if not args.list_file.is_file():
        print(f"Error: list file not found: {args.list_file}", file=sys.stderr)
        sys.exit(2)

    names = read_names(args.list_file)
    if not names:
        print("No filenames found in list file (after ignoring blanks/comments). Nothing to do.")
        sys.exit(0)

    moved, missing, skipped_exists = move_images(
        args.src_dir, names, args.dest_dir, args.overwrite, args.dry_run
    )

    print("\nSummary:")
    print(f"  Moved:          {moved}")
    print(f"  Missing:        {missing}")
    print(f"  Skipped exists: {skipped_exists}")
    if args.strict and missing > 0:
        sys.exit(1)

if __name__ == "__main__":
    main()

'''
python move_images.py /mnt/Data2/luke/pamir/reconstructions/oneframe/Filtered/Combined_exhaustive_incref_filtered/Images \
/mnt/Data2/luke/pamir/reconstructions/oneframe/Filtered/Combined_exhaustive_incref_filtered/bad_imgs.txt \
/mnt/Data2/luke/pamir/reconstructions/oneframe/Filtered/Combined_exhaustive_incref_filtered/bad_images
'''