#!/usr/bin/env python3
"""
Add a prefix to every file in a directory.

Usage:
  python add_prefix.py /path/to/dir PREFIX

Examples:
  python add_prefix.py ./photos abc_
"""

import argparse
from pathlib import Path
import sys

def parse_args():
    p = argparse.ArgumentParser(description="Add a prefix to every file in a directory.")
    p.add_argument("directory", help="Directory containing files to rename")
    p.add_argument("prefix", help="Prefix to add before each filename (e.g., 'abc_')")
    p.add_argument("-n", "--dry-run", action="store_true", help="Show what would be renamed without changing anything")
    return p.parse_args()

def main():
    args = parse_args()
    dir_path = Path(args.directory).expanduser().resolve()

    if not dir_path.is_dir():
        print(f"Error: {dir_path} is not a directory.", file=sys.stderr)
        sys.exit(1)

    files = [p for p in dir_path.iterdir() if p.is_file()]
    if not files:
        print("No files found to rename.")
        return

    renamed = 0
    skipped_already_prefixed = 0
    skipped_conflict = 0

    for p in sorted(files, key=lambda x: x.name.casefold()):
        name = p.name
        if name.startswith(args.prefix):
            skipped_already_prefixed += 1
            continue

        target = p.with_name(args.prefix + name)

        if target.exists():
            # Avoid overwriting; skip this one
            print(f"Skipping (target exists): {p.name} -> {target.name}", file=sys.stderr)
            skipped_conflict += 1
            continue

        if args.dry_run:
            print(f"Would rename: {p.name} -> {target.name}")
        else:
            p.rename(target)
            print(f"Renamed: {p.name} -> {target.name}")
            renamed += 1

    if args.dry_run:
        print(f"\nDry run complete. Would rename {len(files) - skipped_already_prefixed - skipped_conflict} file(s).")
    else:
        print(f"\nDone. Renamed: {renamed}, Skipped (already prefixed): {skipped_already_prefixed}, Skipped (conflict): {skipped_conflict}")

if __name__ == "__main__":
    main()

# python add_prefix.py /mnt/Data2/luke/pamir/reconstructions/oneframe/Filtered/Tiny/Images_2 p2_