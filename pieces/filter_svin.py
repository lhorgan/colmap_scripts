import os

def filter_svin(input_path, output_path, images_set):
    svin_set = set()

    with open(input_path) as f:
        lines = f.readlines()
    
    count = 0
    with open(output_path, "w+") as f:
        comment = lines[0]
        f.write(comment)

        for line in lines[1:]:
            img_name = f'{(line.split(" ")[0]).replace(".", "")}.png'
            svin_set.add(img_name)
            if img_name in images_set:
                #print(img_name, "is in the set")
                count += 1
                f.write(line)
            else:
                #print(f"Did not find {img_name} in the directory. Removing it from SVIN file.")
                pass
    
    print("Added", count)

if __name__ == "main":
    filter_svin(input_path="/home/luke/pamir/Combined_exhaustive/svin.txt", \
                output_path="/home/luke/Documents/Ship/Back/combo/svin.txt", \
                images_path="/home/luke/Documents/Ship/Back/combo/Images")