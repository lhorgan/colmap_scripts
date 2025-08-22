def print_image_info(filename):
    """
    Read a COLMAP images.txt file and print image ID and name for each image.
    
    Args:
        filename (str): Path to the images.txt file
    """
    image_names = set()

    with open(filename, 'r') as f:
        line_count = 0
        
        for line in f:
            # Skip comment lines
            if line.startswith('#'):
                continue
            
            # Strip whitespace
            line = line.strip()
            
            # Skip empty lines
            if not line:
                print("LINE IS BLANK", line_count)
                #continue
            
            # Process only the first line of each image pair (contains the metadata)
            if line_count % 2 == 0:
                # Split the line into parts
                parts = line.split()
                
                if len(parts) >= 10:  # Ensure we have enough fields
                    image_id = parts[0]
                    # NAME is the last field (index 9)
                    name = parts[9]
                    
                    print(f"Line: {line_count} Image ID: {image_id}, Name: {name}")
            
                image_names.add(name)
            
            line_count += 1
    
    print(f"{len(image_names)} images found")

print_image_info("/mnt/Data2/luke/pamir/reconstructions/yes_poses/Pamir2NoTargets/sparse/text/images.txt")