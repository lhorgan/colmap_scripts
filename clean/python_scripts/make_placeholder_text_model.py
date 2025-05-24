import os
import numpy as np
import argparse

def gen_cameras_file(h, w, output_path, cam_file="cameras.txt"):
    # see ~/Documents/colmap/src/colmap/sensor/models.h, line 290
    # see also ~/Documents/pamir/text_pamir1
    # https://colmap.github.io/database.html
    # https://colmap.github.io/cameras.html
    params = {
        "f": 590.34818954980267, 
        "cx": 480, 
        "cy": 270,
        "k": 0.013510657866250657
    }
    
    cam_str = "# Camera list with one line of data per camera:\n"
    cam_str += "# CAMERA_ID, MODEL, WIDTH, HEIGHT, PARAMS[]\n"
    cam_str += "# Number of cameras: 1\n"
    cam_str += f'1 SIMPLE_RADIAL {w} {h} {params["f"]} {params["cx"]} {params["cy"]} {params["k"]}\n'
    cam_params = np.asarray([params["f"], params["cx"], params["cy"], params["k"]])

    with open(os.path.join(output_path,cam_file),'w') as of:
        of.write(cam_str)

    return cam_params

def gen_imgs_file(gt_data_path, colmap_imgs_path, ts):
    count = 0
    img_str = "# Image list with two lines of data per image:\n"
    img_str += "#   IMAGE_ID, QW, QX, QY, QZ, TX, TY, TZ, CAMERA_ID, NAME\n"
    img_str += "#   POINTS2D[] as (X, Y, POINT3D_ID)\n"
    
    with open(gt_data_path, 'r') as file:
        for line_number, line in enumerate(file, start=1):
            line = line.strip()
            line = line.split(" ")
            if '#' in line[0]:
                continue
            if line[0] in ts:
                tx = line[1]
                ty = line[2]
                tz = line[3]
                
                qx = line[4]
                qy = line[5]
                qz = line[6]
                qw = line[7]
                
                imgs_name_list = line[0].split(".")
                imgs_name = imgs_name_list[0] + imgs_name_list[1] + ".png"
    
                img_str += f"{int(count+1)} {qw} {qx} {qy} {qz} {tx} {ty} {tz} 1 {imgs_name}\n\n"
                count += 1

    save_path = os.path.join(colmap_imgs_path, 'images.txt')
    with open(save_path,'w') as of:
        of.write(img_str)
    
    # np.savetxt(save_path, img_str, delimiter=' ', fmt='%f')
    return img_str

def main(args):
    colmap_save_path = args.out_path
    image_path = args.images_path
    cam_poses_path = args.cam_poses

    print(cam_poses_path)

    contents = os.listdir(cam_poses_path)
    print(contents)
    # svin_files = []
    # if os.path.isdir(os.path.join(cam_poses_path, contents[0])):
    #     print("We have a directory, folks.")
    # else:
    #     pass

    return

    contents = os.listdir(image_path)

    contents = os.listdir(image_path)
    if os.path.isdir(os.path.join(image_path, contents[0])):
        image_files = []
        for directory_name in contents:
            directory_path = os.path.join(image_path, directory_name)
            image_names = os.listdir(directory_path)
            image_names = [f"{directory_name}/{image_name}" for image_name in image_names]
            image_files.append(image_names)
    else:
        image_files = [contents]

    for i in range(len(image_files)):
        image_files[i] = [img for img in image_files[i] if img[-3:] == "png"]
        image_files[i].sort()
    
    print(image_files[0])
    
if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("--cam_poses", default="", help="path to the cam poses that will be used for initialization")
    parser.add_argument("--images_path", default="", help="path to the images that will be used by colmap for sparse reconstruction")
    parser.add_argument('--out_path', default="", help="path to the folder where colmap will search for imgs.txt and cams.txt")
    
    args = parser.parse_args()
    main(args)