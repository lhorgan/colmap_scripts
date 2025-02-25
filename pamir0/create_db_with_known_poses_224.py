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

def gen_poses_file(input_path, output_path):
    with open(input_path) as f:
        lines = f.readlines()
    
    comment = lines[0]

    with open(output_path, "w+") as f:
        f.write(comment)
        
        for line in lines[1:]:
            timestamp = line.split(" ")[0]
            img_name = f"{timestamp.replace(".", "")}.png"
            pose = [float(x) for x in (line.split(" ")[1:])]
            tx=pose[0]
            ty=pose[1]
            tz=pose[2]
        
            f.write(f"{img_name} {tx} {ty} {tz}\n")

def gen_database(database_file, cam_params, height, width, image_files, model=1):
    # Open the database.
    db = COLMAPDatabase.connect(database_file)

    # For convenience, try creating all the tables upfront.
    db.create_tables()

    # add camera
    camera_id = db.add_camera(model, width, height, cam_params)

    # Create dummy images.
    for i,img in enumerate(image_files):
        _ = db.add_image(name=img, camera_id=camera_id, image_id=int(i+1))

    # Commit the data to the file.
    db.commit()

    # Clean up.
    db.close()


def main(args):
    colmap_save_path = args.out_path
    image_path = args.images_path
    
    database_file_path = os.path.join(colmap_save_path, 'database.db')
    
    image_files = os.listdir(image_path)
    image_files = [img for img in image_files if img[-3:] == "png"]
    image_files.sort()
    ts = [img.split(".")[0] for img in image_files]
    ts = [t[:10]+'.'+t[10:] for t in ts]

    img = cv2.imread(os.path.join(image_path,image_files[0]))
    height, width, _ = img.shape
    
    cam_params = get_cam_params(height, width)
    
    # model=2 for SIMPLE_RADIAL, see ~/Documents/colmap/src/colmap/sensor/models.h line 83
    gen_database(database_file_path, cam_params, height, width, image_files, model=2) 

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("--images_path", default="", help="path to the images that will be used by colmap for sparse reconstruction")
    parser.add_argument('--out_path', default="", help="path to the folder where colmap will search for imgs.txt and cams.txt")
    
    args = parser.parse_args()
    main(args)
