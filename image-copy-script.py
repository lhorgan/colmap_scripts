#!/usr/bin/env python3

# Courtesy of Claude 3.7

import os
import sys
import shutil
import argparse

def copy_images_except_listed(input_dir, skip_list_file, output_dir):
    """
    Copy images from input_dir to output_dir, except those specified in skip_list_file.
    
    Args:
        input_dir (str): Path to directory containing images to copy
        skip_list_file (str): Path to text file containing names of images to skip (one per line)
        output_dir (str): Path to directory where images should be copied
    """
    # Check if input directory exists
    if not os.path.isdir(input_dir):
        print(f"Error: Input directory '{input_dir}' does not exist.")
        sys.exit(1)
        
    # Check if skip list file exists
    if not os.path.isfile(skip_list_file):
        print(f"Error: Skip list file '{skip_list_file}' does not exist.")
        sys.exit(1)
        
    # Create output directory if it doesn't exist
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        print(f"Created output directory: {output_dir}")
    
    # Read skip list
    with open(skip_list_file, 'r') as f:
        skip_images = [line.strip() for line in f if line.strip()]
    
    # Track which skip images were found
    skip_images_found = set()
    
    # Get all files from input directory
    input_files = os.listdir(input_dir)
    
    # Count how many files we copied
    copied_count = 0
    
    # Process each file in the input directory
    for filename in input_files:
        input_path = os.path.join(input_dir, filename)
        
        # Skip directories
        if os.path.isdir(input_path):
            continue
            
        # Check if this file should be skipped
        if filename in skip_images:
            print(f"Not copying {filename}")
            skip_images_found.add(filename)
            continue
            
        # Copy the file to the output directory
        output_path = os.path.join(output_dir, filename)
        shutil.copy2(input_path, output_path)
        copied_count += 1
    
    # Check if all skip images were found
    for skip_image in skip_images:
        if skip_image not in skip_images_found:
            print(f"Warning: Image to skip '{skip_image}' was not found in the input directory.")
    
    print(f"Copied {copied_count} images from {input_dir} to {output_dir}")
    print(f"Skipped {len(skip_images_found)} images listed in {skip_list_file}")

def main():
    # Set up argument parser
    parser = argparse.ArgumentParser(description='Copy images from one directory to another, excluding specified images.')
    parser.add_argument('input_dir', help='Directory containing images to copy')
    parser.add_argument('skip_list_file', help='Text file containing names of images to skip (one per line)')
    parser.add_argument('output_dir', help='Directory where images should be copied')
    
    # Parse arguments
    args = parser.parse_args()
    
    # Run the main function
    copy_images_except_listed(args.input_dir, args.skip_list_file, args.output_dir)

if __name__ == "__main__":
    main()
