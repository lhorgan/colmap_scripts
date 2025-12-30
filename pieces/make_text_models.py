# With thanks to Claude: https://claude.ai/chat/23a6e096-ae2c-48c6-a500-9fa165330d41

#!/usr/bin/env python3
"""
Recursively find all 'sparse' directories and convert COLMAP binary models to text format.

For each numeric subdirectory (0, 1, 2, etc.) inside a 'sparse' directory that contains
COLMAP bin files, this script runs colmap model_converter to create a 'text' subdirectory
with the text-format model files.
"""

import argparse
import subprocess
import sys
from pathlib import Path


def is_colmap_model_dir(directory: Path) -> bool:
    """Check if a directory contains COLMAP binary model files."""
    required_files = ["cameras.bin", "images.bin", "points3D.bin"]
    return all((directory / f).exists() for f in required_files)


def convert_model_to_text(model_dir: Path, dry_run: bool = False) -> bool:
    """
    Convert a COLMAP binary model to text format.
    
    Args:
        model_dir: Path to the directory containing the binary model
        dry_run: If True, only print the command without executing
        
    Returns:
        True if conversion succeeded, False otherwise
    """
    text_output_dir = model_dir / "text"
    
    # Skip if text directory already exists and has content
    if text_output_dir.exists():
        text_files = ["cameras.txt", "images.txt", "points3D.txt"]
        if all((text_output_dir / f).exists() for f in text_files):
            print(f"  Skipping {model_dir} - text output already exists")
            return True
    
    cmd = [
        "colmap", "model_converter",
        "--input_path", str(model_dir),
        "--output_path", str(text_output_dir),
        "--output_type", "TXT"
    ]
    
    if dry_run:
        print(f"  [DRY RUN] Would run: {' '.join(cmd)}")
        return True
    
    # Create the output directory
    text_output_dir.mkdir(exist_ok=True)
    
    print(f"  Converting {model_dir} -> {text_output_dir}")
    
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=True
        )
        print(f"    Success!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"    Error: {e.stderr}")
        return False
    except FileNotFoundError:
        print("    Error: 'colmap' command not found. Is COLMAP installed and in PATH?")
        return False


def find_and_convert_models(parent_dir: Path, dry_run: bool = False) -> tuple[int, int]:
    """
    Recursively find all 'sparse' directories and convert their COLMAP models.
    
    Args:
        parent_dir: The root directory to search
        dry_run: If True, only print commands without executing
        
    Returns:
        Tuple of (successful conversions, failed conversions)
    """
    success_count = 0
    fail_count = 0
    
    # Find all directories named 'sparse'
    sparse_dirs = list(parent_dir.rglob("sparse"))
    sparse_dirs = [d for d in sparse_dirs if d.is_dir()]
    
    if not sparse_dirs:
        print(f"No 'sparse' directories found under {parent_dir}")
        return 0, 0
    
    print(f"Found {len(sparse_dirs)} 'sparse' directory(ies)")
    
    for sparse_dir in sorted(sparse_dirs):
        print(f"\nProcessing: {sparse_dir}")
        
        # Look for numeric subdirectories (0, 1, 2, etc.) that contain COLMAP models
        model_dirs = []
        for item in sparse_dir.iterdir():
            if item.is_dir() and item.name.isdigit():
                if is_colmap_model_dir(item):
                    model_dirs.append(item)
        
        # Also check if the sparse directory itself is a model directory
        if is_colmap_model_dir(sparse_dir):
            model_dirs.append(sparse_dir)
        
        if not model_dirs:
            print(f"  No COLMAP model directories found in {sparse_dir}")
            continue
        
        for model_dir in sorted(model_dirs):
            if convert_model_to_text(model_dir, dry_run):
                success_count += 1
            else:
                fail_count += 1
    
    return success_count, fail_count


def main():
    parser = argparse.ArgumentParser(
        description="Recursively convert COLMAP binary models to text format"
    )
    parser.add_argument(
        "parent_dir",
        type=Path,
        help="Parent directory to search for 'sparse' folders"
    )
    parser.add_argument(
        "--dry-run", "-n",
        action="store_true",
        help="Print commands without executing them"
    )
    
    args = parser.parse_args()
    
    if not args.parent_dir.exists():
        print(f"Error: Directory '{args.parent_dir}' does not exist")
        sys.exit(1)
    
    if not args.parent_dir.is_dir():
        print(f"Error: '{args.parent_dir}' is not a directory")
        sys.exit(1)
    
    print(f"Searching for COLMAP models in: {args.parent_dir.resolve()}")
    if args.dry_run:
        print("(Dry run mode - no changes will be made)\n")
    
    success, fail = find_and_convert_models(args.parent_dir, args.dry_run)
    
    print(f"\n{'=' * 50}")
    print(f"Conversion complete: {success} succeeded, {fail} failed")
    
    if fail > 0:
        sys.exit(1)


if __name__ == "__main__":
    main()