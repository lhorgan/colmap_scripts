#!/usr/bin/env python3
"""
Select a window of images around a target image (n1 before, the image itself,
and n2 after) based on alphabetical order, and copy them to an output directory.

Usage:
  python select_images.py INPUT_DIR OUTPUT_DIR IMAGE_NAME N1 N2

Notes:
- Sorting is case-insensitive alphabetical by filename.
- IMAGE_NAME should match a filename in INPUT_DIR. If you omit the extension and
  there is exactly one file with that stem, it will be used.
- N1 and N2 must be non-negative integers.
"""

import argparse
import shutil
import sys
from pathlib import Path
import difflib

def nonneg_int(s: str) -> int:
    try:
        v = int(s)
    except ValueError:
        raise argparse.ArgumentTypeError(f"Expected a non-negative integer, got {s!r}")
    if v < 0:
        raise argparse.ArgumentTypeError(f"Expected a non-negative integer, got {v}")
    return v

def parse_args():
    p = argparse.ArgumentParser(description="Copy a window of images around a given image.")
    p.add_argument("input_dir", help="Directory containing source images")
    p.add_argument("output_dir", help="Empty directory to receive copies")
    p.add_argument("image_name", help="The filename of the center image (e.g., mypic.jpg)")
    p.add_argument("n1", type=nonneg_int, help="How many images BEFORE to include (>= 0)")
    p.add_argument("n2", type=nonneg_int, help="How many images AFTER to include (>= 0)")
    return p.parse_args()

def resolve_target_index(files, target_name):
    # Exact match first
    try:
        return files.index(target_name)
    except ValueError:
        pass

    # If no extension provided, try unique stem match
    if "." not in target_name:
        matches = [f for f in files if Path(f).stem == target_name]
        if len(matches) == 1:
            return files.index(matches[0])

    return None

def main():
    args = parse_args()
    in_dir = Path(args.input_dir).expanduser().resolve()
    out_dir = Path(args.output_dir).expanduser().resolve()

    if not in_dir.is_dir():
        print(f"Error: Input directory not found: {in_dir}", file=sys.stderr)
        sys.exit(1)

    if in_dir == out_dir:
        print("Error: Output directory must be different from input directory.", file=sys.stderr)
        sys.exit(1)

    out_dir.mkdir(parents=True, exist_ok=True)

    # Gather files and sort case-insensitively by name
    files = [p.name for p in in_dir.iterdir() if p.is_file()]
    if not files:
        print(f"Error: No files found in input directory: {in_dir}", file=sys.stderr)
        sys.exit(1)

    files.sort(key=lambda s: (s.casefold(), s))

    idx = resolve_target_index(files, args.image_name)
    if idx is None:
        print(f"Error: Could not find image {args.image_name!r} in {in_dir}", file=sys.stderr)
        suggestions = difflib.get_close_matches(args.image_name, files, n=5)
        if suggestions:
            print("Did you mean one of:", file=sys.stderr)
            for s in suggestions:
                print(f"  - {s}", file=sys.stderr)
        else:
            print("No similar filenames found.", file=sys.stderr)
        sys.exit(1)

    start = max(0, idx - args.n1)
    end = min(len(files), idx + args.n2 + 1)  # slice end is exclusive
    selected = files[start:end]

    # Copy
    for name in selected:
        src = in_dir / name
        dst = out_dir / name
        shutil.copy2(src, dst)

    print(f"Copied {len(selected)} file(s) to {out_dir}:")
    for name in selected:
        print(f"  {name}")

if __name__ == "__main__":
    main()

'''
python select_images.py /mnt/Data2/luke/pamir/reconstructions/oneframe/Filtered/Pamir1/Images \
    /mnt/Data2/luke/pamir/reconstructions/oneframe/Filtered/Mid1/Images \
    1737456763565105333.png \
    100 100

python select_images.py /mnt/Data2/luke/pamir/reconstructions/oneframe/Filtered/Pamir2/Images \
    /mnt/Data2/luke/pamir/reconstructions/oneframe/Filtered/Mid2/Images \
    1737461321750802666.png \
    100 100
'''