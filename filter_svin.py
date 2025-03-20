import os

def filter_svin(input_path, output_path, images_path):
    images_set = set()
    for img_name in os.listdir(images_path):
        images_set.add(img_name)
    print(len(images_set))

    with open(input_path) as f:
        lines = f.readlines()
    
    count = 0
    with open(output_path, "w+") as f:
        comment = lines[0]
        f.write(comment)

        for line in lines[1:]:
            img_name = f'{(line.split(" ")[0]).replace(".", "")}.png'
            if img_name in images_set:
                #print(img_name, "is in the set")
                count += 1
                f.write(line)
            else:
                print(f"Did not find {img_name}.")
    
    print("Added", count)

filter_svin(input_path="/home/luke/Documents/camera_plotter/svin_Pamir1_full.txt", \
            output_path="/home/luke/Documents/pamir_reconstructions/feb28/full/Pamir1kf/svin.txt", \
            images_path="/home/luke/Documents/pamir_reconstructions/feb28/full/Pamir1kf/Images")