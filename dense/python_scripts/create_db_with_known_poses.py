#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Sep 23 10:42:02 2024

@author: harish
"""

import os
import numpy as np
from scipy.spatial.transform import Rotation as R
import cv2
import argparse
from create_database import COLMAPDatabase

def get_cam_params(h, w):
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
    #cam_str += "1 SIMPLE_RADIAL 960 540 590.34818954980267 480 270 0.013510657866250657"
    cam_str += f"1 SIMPLE_RADIAL {w} {h} {params["f"]} {params["cx"]} {params["cy"]} {params["k"]}\n"
    cam_params = np.asarray([params["f"], params["cx"], params["cy"], params["k"]])

    return cam_params

def gen_cameras_file(h, w, output_path, cam_file="cameras.txt", count=1):
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
    #cam_str += "1 SIMPLE_RADIAL 960 540 590.34818954980267 480 270 0.013510657866250657"
    for id in range(1, 4):
        cam_str += f'{id} SIMPLE_RADIAL {w} {h} {params["f"]} {params["cx"]} {params["cy"]} {params["k"]}\n'

    with open(os.path.join(output_path,cam_file),'w') as of:
        of.write(cam_str)

def gen_poses_file_from_svin(input_path, output_path):
    if os.path.isdir(input_path):
        filenames = os.listdir(input_path)
        for filename in filenames:
            gen_poses_file_from_svin_helper(input_path=os.path.join(input_path, filename), \
                                            output_path=output_path, \
                                            img_name_prefix=f"{filename.replace(".txt", "")}/")
    else:
        gen_poses_file_from_svin_helper(input_path, output_path)

def gen_poses_file_from_svin_helper(input_path, output_path, img_name_prefix=""):
    with open(input_path) as f:
        lines = f.readlines()

    with open(output_path, "a+") as f:        
        for line in lines[1:]:
            timestamp = line.split(" ")[0]
            img_name = f"{timestamp.replace(".", "")}.png"
            pose = [float(x) for x in (line.split(" ")[1:])]
            tx=pose[0]
            ty=pose[1]
            tz=pose[2]
        
            f.write(f"{img_name_prefix}{img_name} {tx} {ty} {tz}\n")

def gen_poses_file_from_colmap_output(input_path, output_path):
    with open(input_path) as f:
        lines = f.readlines()
    
    with open(output_path, "w+") as f:
        should_skip = False
        for line in lines:
            if line[0] == "#":
                continue

            if should_skip:
                should_skip = False
            else:
                # IMAGE_ID, QW, QX, QY, QZ, TX, TY, TZ, CAMERA_ID, NAME
                line_parts = line.strip().split(" ")
                tx = float(line_parts[5])
                ty = float(line_parts[6])
                tz = float(line_parts[7])
                img_name = line_parts[9]
                #print(line)

                f.write(f"{img_name} {tx} {ty} {tz}\n")
                
                should_skip = True

def gen_text_model(input_path, output_path):
    print(f"Writing placeholder text file to {output_path} using poses from {input_path}.")
    svin_filenames = os.listdir(input_path)
    print(svin_filenames)
    
    img_str = "# Image list with two lines of data per image:\n"
    img_str += "#   IMAGE_ID, QW, QX, QY, QZ, TX, TY, TZ, CAMERA_ID, NAME\n"
    img_str += "#   POINTS2D[] as (X, Y, POINT3D_ID)\n"

    camera_id = 1
    count = 0
    for filename in svin_filenames:
        with open(os.path.join(input_path, filename), "r") as file:
            for line_number, line in enumerate(file, start=1):
                line = line.strip()
                line = line.split(" ")
                if line[0][0] == "#":
                    continue
                
                tx = line[1]
                ty = line[2]
                tz = line[3]
                
                qx = line[4]
                qy = line[5]
                qz = line[6]
                qw = line[7]

                imgs_name_list = line[0].split(".")
                imgs_name = imgs_name_list[0] + imgs_name_list[1] + ".png"
                if len(svin_filenames) > 0:
                    name_prefix = filename.split(".")[0]
                    imgs_name = name_prefix + "/" + imgs_name
    
                img_str += f"{int(count+1)} {qw} {qx} {qy} {qz} {tx} {ty} {tz} {camera_id} {imgs_name}\n\n"
                count += 1
        camera_id += 1
    
    save_path = os.path.join(output_path, "images.txt")
    print(f"writing images.txt to {output_path}")
    with open(save_path,'w') as of:
        of.write(img_str)

def gen_database(database_file, cam_params, height, width, image_files, model=1):
    # Open the database.
    db = COLMAPDatabase.connect(database_file)

    # For convenience, try creating all the tables upfront.
    db.create_tables()

    # add camera
    id = 1
    for directory in image_files:
        camera_id = db.add_camera(model, width, height, cam_params)
        
        # Create dummy images.
        for img in directory:
            #print(f"adding image {img} with id {id}")
            _ = db.add_image(name=img, camera_id=camera_id, image_id=int(id))
            id += 1

    # Commit the data to the file.
    db.commit()

    # Clean up.
    db.close()


def main(args):
    colmap_save_path = args.out_path
    image_path = args.images_path
    
    database_file_path = os.path.join(args.base_path, 'database.db')
    
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

    img = cv2.imread(os.path.join(image_path, image_files[0][0]))
    height, width, _ = img.shape
    
    cam_params = get_cam_params(height, width)

    print("Generating cam poses from non-inverted SVIN file")
    gen_poses_file_from_svin(input_path=args.cam_poses, output_path=os.path.join(colmap_save_path, "poses.txt"))
        
    # model=2 for SIMPLE_RADIAL, see ~/Documents/colmap/src/colmap/sensor/models.h line 83

    gen_database(database_file_path, cam_params, height, width, image_files, model=2) 

    if args.text_model is not None:
        gen_text_model(args.cam_poses_inv, args.text_model)
        gen_cameras_file(height, width, args.text_model, count=len(image_files))
        fp = open(os.path.join(args.text_model,"points3D.txt"),'w')
        fp.close()


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("--text_model", required=False, help="path to the placeholder text model")
    parser.add_argument("--images_path", default="", help="path to the images that will be used by colmap for sparse reconstruction")
    parser.add_argument('--out_path', default="", help="path to the folder where colmap will search for imgs.txt and cams.txt")
    parser.add_argument('--cam_poses_inv', default="", help="path to the inverted svin file")
    parser.add_argument('--cam_poses', default="", help="path to the raw svin file")
    parser.add_argument('--base_path', default="", help="path to the data")
    
    args = parser.parse_args()
    main(args)
