#!/usr/bin/env python3
"""
Filter a COLMAP database to a subset of images.

Usage:
    python filter_colmap_db.py input.db output.db /path/to/image/subset/
"""

# This script is written by Claude.
# https://claude.ai/chat/69336946-4a19-40d4-8bbf-7646c2e06fae

import argparse
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
    src = sqlite3.connect(input_db)
    dst = sqlite3.connect(output_db)
    
    src_cursor = src.cursor()
    dst_cursor = dst.cursor()
    
    try:
        # Copy schema from source (excluding sqlite internal tables)
        src_cursor.execute("""
            SELECT sql FROM sqlite_master 
            WHERE type='table' 
            AND sql IS NOT NULL 
            AND name NOT LIKE 'sqlite_%'
        """)
        for (schema,) in src_cursor.fetchall():
            dst_cursor.execute(schema)
        
        # Copy cameras table entirely
        src_cursor.execute("SELECT * FROM cameras")
        cameras = src_cursor.fetchall()
        if cameras:
            placeholders = ",".join("?" * len(cameras[0]))
            dst_cursor.executemany(f"INSERT INTO cameras VALUES ({placeholders})", cameras)
        
        # Get image_ids to keep
        src_cursor.execute("SELECT image_id, name FROM images")
        all_images = src_cursor.fetchall()
        images_to_keep = [(img_id, name) for img_id, name in all_images if name in image_names]
        ids_to_keep = [img_id for img_id, _ in images_to_keep]
        
        if ids_to_keep:
            placeholders = ",".join("?" * len(ids_to_keep))
            
            # Tables that filter by image_id
            tables_to_filter = ["images", "keypoints", "descriptors", "pose_priors"]
            
            for table in tables_to_filter:
                src_cursor.execute(f"SELECT * FROM {table} WHERE image_id IN ({placeholders})", ids_to_keep)
                rows = src_cursor.fetchall()
                if rows:
                    row_placeholders = ",".join("?" * len(rows[0]))
                    dst_cursor.executemany(f"INSERT INTO {table} VALUES ({row_placeholders})", rows)
        
        # matches, two_view_geometries are left empty
        
        dst.commit()
        
        kept = len(images_to_keep)
        removed = len(all_images) - kept
        print(f"Kept {kept} images, skipped {removed}")
        
    finally:
        src.close()
        dst.close()


def main():
    parser = argparse.ArgumentParser(description="Filter COLMAP database to image subset")
    parser.add_argument("input_db", type=Path, help="Input COLMAP database (will NOT be modified)")
    parser.add_argument("output_db", type=Path, help="Output filtered database")
    parser.add_argument("image_dir", type=Path, help="Directory containing the subset of images to keep")
    
    args = parser.parse_args()
    
    if not args.image_dir.is_dir():
        raise NotADirectoryError(f"Not a directory: {args.image_dir}")
    
    image_names = get_image_names(args.image_dir)
    print(f"Found {len(image_names)} images in {args.image_dir}")
    
    if args.output_db.exists():
        raise FileExistsError(f"Output database already exists: {args.output_db}")
    
    filter_database(args.input_db, args.output_db, image_names)
    print(f"Filtered database written to {args.output_db}")


if __name__ == "__main__":
    main()