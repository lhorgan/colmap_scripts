from __future__ import annotations

#!/usr/bin/env python3

# https://claude.ai/chat/69336946-4a19-40d4-8bbf-7646c2e06fae

"""
Filter a COLMAP database to a subset of images.

Usage:
    python filter_colmap_db.py input.db output.db /path/to/image/subset/
"""

import argparse
import shutil
import sqlite3
from pathlib import Path

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".tif", ".tiff", ".bmp", ".webp"}


def get_image_names(image_dir: Path) -> set[str]:
    """Get all image filenames from a directory."""
    names = set()
    for path in image_dir.iterdir():
        if path.suffix.lower() in IMAGE_EXTENSIONS:
            names.add(path.name)
    return names


def filter_database(input_db: Path, output_db: Path, image_names: set[str]) -> None:
    # Copy the database first - input remains untouched
    shutil.copy2(input_db, output_db)
    
    conn = sqlite3.connect(output_db)
    cursor = conn.cursor()
    
    try:
        # Clear tables that should be fully wiped
        cursor.execute("DELETE FROM matches")
        cursor.execute("DELETE FROM pose_priors")
        cursor.execute("DELETE FROM two_view_geometries")
        
        # Get image_ids to remove (images NOT in our list)
        cursor.execute("SELECT image_id, name FROM images")
        all_images = cursor.fetchall()
        
        ids_to_remove = [img_id for img_id, name in all_images if name not in image_names]
        
        if ids_to_remove:
            placeholders = ",".join("?" * len(ids_to_remove))
            
            # Remove from images table
            cursor.execute(f"DELETE FROM images WHERE image_id IN ({placeholders})", ids_to_remove)
            
            # Remove orphaned keypoints and descriptors
            cursor.execute(f"DELETE FROM keypoints WHERE image_id IN ({placeholders})", ids_to_remove)
            cursor.execute(f"DELETE FROM descriptors WHERE image_id IN ({placeholders})", ids_to_remove)
        
        conn.commit()
        
        # Report what happened
        kept = len(all_images) - len(ids_to_remove)
        print(f"Kept {kept} images, removed {len(ids_to_remove)}")
        
    finally:
        cursor.execute("VACUUM")
        conn.close()


def main():
    parser = argparse.ArgumentParser(description="Filter COLMAP database to image subset")
    parser.add_argument("input_db", type=Path, help="Input COLMAP database (will NOT be modified)")
    parser.add_argument("output_db", type=Path, help="Output filtered database")
    parser.add_argument("image_dir", type=Path, help="Directory containing the subset of images to keep")
    
    args = parser.parse_args()
    
    if not args.image_dir.is_dir():
        raise NotADirectoryError(f"Not a directory: {args.image_dir}")
    
    # Get image names from directory
    image_names = get_image_names(args.image_dir)
    print(f"Found {len(image_names)} images in {args.image_dir}")
    
    if args.output_db.exists():
        raise FileExistsError(f"Output database already exists: {args.output_db}")
    
    filter_database(args.input_db, args.output_db, image_names)
    print(f"Filtered database written to {args.output_db}")


if __name__ == "__main__":
    main()

# python filter_colmap_db.py /home/luke/Documents/peace2/peace/Database/database.db /home/luke/Documents/peace2/peace/spheres/cluster_3/database.db /home/luke/Documents/peace2/peace/spheres/cluster_3/Images