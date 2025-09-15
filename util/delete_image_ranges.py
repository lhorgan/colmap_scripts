# This file was written by Claude.  Thanks Claude.

#!/usr/bin/env python3
"""
Script to delete images within specified ranges based on a text file.

Usage: python delete_image_ranges.py <text_file_path> <image_directory_path>
"""

import os
import sys
import argparse
from pathlib import Path
from typing import List, Tuple, Set


def load_and_sort_images(directory_path: Path) -> List[str]:
    """
    Load all image filenames from the directory and sort them alphabetically.
    
    Args:
        directory_path: Path to the directory containing images
        
    Returns:
        Sorted list of image filenames
    """
    # Common image extensions
    image_extensions = {'.png', '.jpg', '.jpeg', '.gif', '.bmp', '.tiff', '.tif', '.webp'}
    
    images = []
    for file in directory_path.iterdir():
        if file.is_file() and file.suffix.lower() in image_extensions:
            images.append(file.name)
    
    # Sort alphabetically (case-sensitive by default, which is standard)
    images.sort()
    return images


def parse_ranges_file(file_path: Path) -> List[Tuple[str, str]]:
    """
    Parse the text file to extract image range pairs.
    
    Args:
        file_path: Path to the text file containing ranges
        
    Returns:
        List of tuples, each containing (start_image, end_image)
    """
    ranges = []
    
    with open(file_path, 'r') as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            
            # Skip empty lines
            if not line:
                continue
            
            # Split the line into two image names
            parts = line.split()
            
            if len(parts) != 2:
                print(f"Warning: Line {line_num} does not contain exactly 2 image names: '{line}'")
                continue
            
            ranges.append((parts[0], parts[1]))
    
    return ranges


def find_images_in_range(all_images: List[str], start_img: str, end_img: str) -> Set[str]:
    """
    Find all images that fall within the specified range (inclusive).
    
    Args:
        all_images: Sorted list of all image names
        start_img: Starting image name (inclusive)
        end_img: Ending image name (inclusive)
        
    Returns:
        Set of image names within the range
    """
    images_to_delete = set()
    
    # Find if start and end images exist in the list
    in_range = False
    
    for img in all_images:
        # Check if we've reached the start of the range
        if img == start_img:
            in_range = True
        
        # If we're in range, add to deletion set
        if in_range:
            images_to_delete.add(img)
        
        # Check if we've reached the end of the range
        if img == end_img:
            break
    
    # Handle case where images are compared alphabetically even if not in list
    # This handles the case where range boundaries might not exist in directory
    if not images_to_delete:
        for img in all_images:
            if start_img <= img <= end_img:
                images_to_delete.add(img)
    
    return images_to_delete


def delete_images(directory_path: Path, images_to_delete: Set[str], dry_run: bool = False):
    """
    Delete the specified images from the directory.
    
    Args:
        directory_path: Path to the directory containing images
        images_to_delete: Set of image filenames to delete
        dry_run: If True, only print what would be deleted without actually deleting
    """
    deleted_count = 0
    
    for img_name in sorted(images_to_delete):
        img_path = directory_path / img_name
        
        if img_path.exists():
            if dry_run:
                print(f"  [DRY RUN] Would delete: {img_name}")
            else:
                try:
                    img_path.unlink()
                    print(f"  Deleted: {img_name}")
                    deleted_count += 1
                except Exception as e:
                    print(f"  Error deleting {img_name}: {e}")
        else:
            print(f"  Warning: {img_name} not found in directory")
    
    if not dry_run:
        print(f"\nTotal files deleted: {deleted_count}")
    else:
        print(f"\n[DRY RUN] Would delete {len(images_to_delete)} files total")


def main():
    parser = argparse.ArgumentParser(
        description="Delete images within ranges specified in a text file"
    )
    parser.add_argument("text_file", help="Path to text file containing image ranges")
    parser.add_argument("image_directory", help="Path to directory containing images")
    parser.add_argument(
        "--dry-run", 
        action="store_true", 
        help="Show what would be deleted without actually deleting"
    )
    parser.add_argument(
        "--confirm", 
        action="store_true", 
        help="Skip confirmation prompt"
    )
    
    args = parser.parse_args()
    
    # Convert to Path objects
    text_file_path = Path(args.text_file)
    image_dir_path = Path(args.image_directory)
    
    # Validate paths
    if not text_file_path.exists():
        print(f"Error: Text file '{text_file_path}' does not exist")
        sys.exit(1)
    
    if not image_dir_path.exists() or not image_dir_path.is_dir():
        print(f"Error: Directory '{image_dir_path}' does not exist or is not a directory")
        sys.exit(1)
    
    print(f"Text file: {text_file_path}")
    print(f"Image directory: {image_dir_path}")
    print()
    
    # Load and sort images
    all_images = load_and_sort_images(image_dir_path)
    print(f"Found {len(all_images)} images in directory")
    
    # Parse ranges from text file
    ranges = parse_ranges_file(text_file_path)
    print(f"Found {len(ranges)} range(s) in text file")
    print()
    
    # Collect all images to delete
    all_images_to_delete = set()
    
    for i, (start_img, end_img) in enumerate(ranges, 1):
        print(f"Range {i}: {start_img} to {end_img}")
        images_in_range = find_images_in_range(all_images, start_img, end_img)
        
        if images_in_range:
            print(f"  Found {len(images_in_range)} image(s) in this range")
            all_images_to_delete.update(images_in_range)
        else:
            print(f"  No images found in this range")
    
    print()
    
    if not all_images_to_delete:
        print("No images to delete")
        return
    
    print(f"Total unique images to delete: {len(all_images_to_delete)}")
    
    # Confirmation prompt (unless skipped or dry run)
    if not args.dry_run and not args.confirm:
        print("\nImages that will be deleted:")
        for img in sorted(all_images_to_delete)[:10]:
            print(f"  - {img}")
        if len(all_images_to_delete) > 10:
            print(f"  ... and {len(all_images_to_delete) - 10} more")
        
        response = input("\nDo you want to proceed with deletion? (yes/no): ").strip().lower()
        if response not in ['yes', 'y']:
            print("Deletion cancelled")
            return
    
    print("\nDeleting images...")
    delete_images(image_dir_path, all_images_to_delete, dry_run=args.dry_run)


if __name__ == "__main__":
    main()