import os

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
            line_parts = line.split(" ")
            image_name = line_parts[0]
            new_line = " ".join([f"{images_dir_name}/{image_name}"] + line_parts[1:])
            print(new_line)
            svin_lines.append(new_line)
    
    with open(output_filename, "w+") as f:
        f.writelines(lines)

combine_svin(["/home/luke/Documents/hell/svin_CenterSynced.txt"], ["/home/luke/Documents/hell/First500/Images/Center"])