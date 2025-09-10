import os

def filter_svin(input_path, output_path, images_path):
    images_set = set()
    svin_set = set()

    for img_name in os.listdir(images_path):
        images_set.add(img_name)
    print(len(images_set))

    with open(input_path, "r") as f:
        lines = f.readlines()

    for line in lines[1:]:
        img_name = f'{(line.split(" ")[0]).replace(".", "")}.png'
        svin_set.add(img_name)
    
    both_set = svin_set & images_set

    removed_svin_cnt = 0
    added_svin_cnt = 0
    with open(output_path, "w+") as f:
        comment = lines[0]
        f.write(comment)
        
        for line in lines[1:]:
            img_name = f'{(line.split(" ")[0]).replace(".", "")}.png'
            if img_name in both_set:
                f.write(line)
                added_svin_cnt += 1
            else:
                removed_svin_cnt += 1

    removed_img_count = 0
    added_img_count = 0
    for img_name in os.listdir(images_path):
        if img_name not in both_set:
            removed_img_count += 1
            #os.remove(f"{images_path}/{img_name}")
        else:
            added_img_count += 1
    
    print(f"Removed {removed_svin_cnt} SVIN poses.  Kept {added_svin_cnt} SVIN poses.")
    print(f"Removed {removed_img_count} images.  Kept {added_img_count} images.")
    print(f"Set intersection size: {len(both_set)}")

filter_svin(input_path="/mnt/Data3/luke/underwater/reconstructions/Pamir2/svin_orig.txt", \
            output_path="/mnt/Data3/luke/underwater/reconstructions/Pamir2/svin_orig_filtered.txt", \
            images_path="/mnt/Data3/luke/underwater/reconstructions/Pamir2/Images")