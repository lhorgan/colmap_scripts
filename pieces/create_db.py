#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Sep 23 10:42:02 2024

@author: harish
"""

import os
import numpy as np
import cv2
import argparse
from create_database import COLMAPDatabase

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
    #cam_str += "1 SIMPLE_RADIAL 960 540 590.34818954980267 480 270 0.013510657866250657"
    cam_str += f'1 SIMPLE_RADIAL {w} {h} {params["f"]} {params["cx"]} {params["cy"]} {params["k"]}\n'
    cam_params = np.asarray([params["f"], params["cx"], params["cy"], params["k"]])

    with open(os.path.join(output_path,cam_file),'w') as of:
        of.write(cam_str)

    return cam_params

def gen_database(database_file, cam_params, height, width, image_files, model=1):
    # Open the database.
    db = COLMAPDatabase.connect(database_file)

    # For convenience, try creating all the tables upfront.
    db.create_tables()

    # add camera
    camera_id = db.add_camera(model, width, height, cam_params)

    existing_images = db.read_images()
    existing_image_names = set()
    for _, image_name in existing_images:
        existing_image_names.add(image_name)

    # Create dummy images.
    for i,img in enumerate(image_files):
        if img not in existing_image_names:
            _ = db.add_image(name=img, camera_id=camera_id, image_id=int(i+1))
        else:
            print(f"Skipping {img} because it already exists.")

    # Commit the data to the file.
    db.commit()

    # Clean up.
    db.close()

def main(args):
    colmap_save_path = args.out_path
    image_path = args.images_path
    database_file_path = colmap_save_path.split("/")
    database_path = database_file_path[1:-2]

    database_file_path = os.path.join('/',*database_path, 'database.db')
    
    image_files = os.listdir(image_path)
    image_files = [img for img in image_files if img[-3:] == "png" ]
    image_files.sort()

    # create cameras file
    img = cv2.imread(os.path.join(image_path,image_files[0]))
    height, width, _ = img.shape
    
    cam_params = gen_cameras_file(height, width, colmap_save_path)
    
    fp = open(os.path.join(colmap_save_path, "points3D.txt"), 'w')
    fp.close()

    fp = open(os.path.join(colmap_save_path, "images.txt"), 'w')
    fp.close()
    
    gen_database(database_file_path, cam_params, height, width, image_files, model=2) # two for SIMPLE_RADIAL, see ~/Documents/colmap/src/colmap/sensor/models.h line 83

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--images_path', help="path to the images that will be used by colmap for sparse reconstruction")
    parser.add_argument('--out_path', help="path to the folder where colmap will search for imgs.txt and cams.txt")
    
    args = parser.parse_args()
    main(args)
