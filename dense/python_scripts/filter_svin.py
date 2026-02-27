import os
import argparse

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
                count += 1
                f.write(line)
            else:
                print(f"Did not find {img_name}.")
    
    print("Added", count)

def main():
    parser = argparse.ArgumentParser(description='Filter SVIN data based on available images')
    parser.add_argument('--input', '-i', dest='input_path', required=True, help='Path to the input SVIN file')
    parser.add_argument('--output', '-o', dest='output_path', required=True, help='Path where filtered SVIN will be saved')
    parser.add_argument('--images', '-img', dest='images_path', required=True, help='Path to the directory containing images')
    
    args = parser.parse_args()
    
    filter_svin(args.input_path, args.output_path, args.images_path)

if __name__ == "__main__":
    main()