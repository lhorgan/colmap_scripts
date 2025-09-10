import os

def filter_svin(input_path, output_path, images_path):
    images_set = set()
    svin_set = set()

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
            svin_set.add(img_name)
            if img_name in images_set:
                #print(img_name, "is in the set")
                count += 1
                f.write(line)
            else:
                print(f"Did not find {img_name} in the directory. Removing it from SVIN file.")
    
    print("Added", count)

# filter_svin(input_path="/mnt/Data2/luke/pamir/oneframe2/Pamir012/PamirCombined/svin_inv_full.txt", \
#             output_path="/mnt/Data2/luke/pamir/oneframe2/Pamir012/PamirCombined/svin.txt", \
#             images_path="/mnt/Data2/luke/pamir/oneframe2/Pamir012/PamirCombined/Images")

# filter_svin(input_path="/mnt/Data2/luke/pamir/reconstructions/oneframe/Filtered/Combined/svin.txt", \
#             output_path="/mnt/Data2/luke/pamir/reconstructions/oneframe/Filtered/Combined_exhaustive_incref_filtered/svin.txt", \
#             images_path="/mnt/Data2/luke/pamir/reconstructions/oneframe/Filtered/Combined_exhaustive_incref_filtered/Images")

# filter_svin(input_path="/mnt/Data2/luke/pamir/reconstructions/oneframe/Filtered/Combined/svin.txt", \
#             output_path="/mnt/Data2/luke/pamir/reconstructions/oneframe/Filtered/Mid2/svin.txt", \
#             images_path="/mnt/Data2/luke/pamir/reconstructions/oneframe/Filtered/Mid2/Images")

# filter_svin(input_path="/mnt/Data2/luke/pamir/reconstructions/oneframe/Pamir/Pamir2/Pamir2_transformed_backup.txt", \
#             output_path="/mnt/Data2/luke/pamir/reconstructions/oneframe/Filtered/Mid1/svin_noninv.txt", \
#             images_path="/mnt/Data2/luke/pamir/reconstructions/oneframe/Filtered/Mid1/Images")

# filter_svin(input_path="/mnt/Data2/luke/pamir/reconstructions/oneframe/Filtered/Combined/svin.txt", \
#             output_path="/mnt/Data3/luke/underwater/matchmania/MatchedSeq/matched/Combined/svin.txt", \
#             images_path="/mnt/Data3/luke/underwater/matchmania/MatchedSeq/matched/Combined/Images")

filter_svin(input_path="/mnt/Data3/luke/underwater/matchmania/MatchedSeq/matched/Combined/svin.txt", \
            output_path="/mnt/Data3/luke/underwater/matchmania/MatchedSeq/matched/Just2/svin.txt", \
            images_path="/mnt/Data3/luke/underwater/matchmania/MatchedSeq/matched/Just2/Images")