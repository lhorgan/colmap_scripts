import os
import argparse

def combine_svin(svin_dir, images_dir, output_filename):
    svin_paths = [os.path.join(svin_dir, name) for name in os.listdir(svin_dir)]
    images_paths = [os.path.join(images_dir, name) for name in os.listdir(images_dir)]

    svin_lines = []
    
    for i in range(len(svin_paths)):
        svin_path = svin_paths[i]
        images_path = images_paths[i]
        images_dir_name = os.path.basename(images_path)

        with open(svin_path) as f:
            lines = f.readlines()[1:]
        
        for line in lines:
            #timestamp tx ty tz qx qy qz qw
            line_parts = line.split(" ")
            timestamp, tx, ty, tz, qx, qy, qz, qw = line_parts
            image_name = f"{images_dir_name}/{line_parts[0].replace(".", "")}.png"
            svin_line = []
    
    # IMAGE_ID, QW, QX, QY, QZ, TX, TY, TZ, CAMERA_ID, NAME
    # Then a newline
    with open(output_filename, "w+") as f:
        f.write("# IMAGE_ID, QW, QX, QY, QZ, TX, TY, TZ, CAMERA_ID, NAME\n")
        f.writelines(lines)

def main(args):
    combine_svin(svin_dir=args.svin_path, images_dir=args.images_path, output_filename=args.output_filename)

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("--svin_path", default="", help="")
    parser.add_argument("--images_path", default="", help="")
    parser.add_argument("--output_filename", default="", help="")
    
    args = parser.parse_args()
    main(args)