#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Sep 23 10:42:02 2024

@author: harish
"""

import sys, os
import sqlite3
import numpy as np
import cv2
import argparse
from create_database import COLMAPDatabase
import torch
from pytorch3d.transforms import quaternion_to_matrix, matrix_to_quaternion

def invert_cam_extrinsics(trans, quat):
    trans_torch = torch.from_numpy(trans)
    quat_torch = torch.from_numpy(quat)
    rot_torch = quaternion_to_matrix(quat_torch)
    ext_mat_torch = torch.cat((rot_torch, trans_torch), dim=1)
    last_col = np.asarray([[0,0,0,1]])
    last_col_torch = torch.from_numpy(last_col)
    ext_mat_torch = torch.cat((ext_mat_torch, last_col_torch), dim=0)
    inv_ext_mat_torch = ext_mat_torch.inverse()
    inv_rot_mat = inv_ext_mat_torch[:3, :3]
    inv_trans = (inv_ext_mat_torch[:3,3].numpy()).squeeze()
    inv_quat = matrix_to_quaternion(inv_rot_mat)
    inv_quat = (inv_quat.numpy()).squeeze()
    qx = str(inv_quat[1])
    qy = str(inv_quat[2])
    qz = str(inv_quat[3])
    qw = str(inv_quat[0])
    q = np.asarray([qw, qx, qy, qz])

    tx = str(inv_trans[0])
    ty = str(inv_trans[1])
    tz = str(inv_trans[2])
    t = np.asarray([tx, ty, tz])

    return q, t


def gen_cameras_file(h, w, output_path, cam_file="cameras.txt"):
    cams = [590.248131, 480, 270, 0.014497454110629953, 0.000000, 0.000000, 0.000000]
    w = 960
    h = 540
    
    cam_str = "# Camera list with one line of data per camera:\n"
    cam_str += "# CAMERA_ID, MODEL, WIDTH, HEIGHT, PARAMS[]\n"
    cam_str += "# Number of cameras: 1\n"
    cam_str += f"1 SIMPLE_RADIAL {w} {h} {cams[0]} {cams[1]} {cams[2]} {cams[3]}\n"
    cam_params = np.asarray([cams[0], cams[1], cams[2], cams[3]])

    with open(os.path.join(output_path,cam_file),'w') as of:
        of.write(cam_str)

    return cam_params

def gen_imgs_file(gt_data_path, colmap_imgs_path, ts):
    count_cams = 0
    # -1 is because of pairs.txt. Need a better way to initialize this size
    
    rotation_matrix = np.zeros((3, 3))
    translation_vec = np.zeros(3)
    cam_id = 1
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

                trans = np.asarray([[float(tx)], [float(ty)], [float(tz)]])
                quat = np.asarray([float(qw), float(qx), float(qy), float(qz)])
                
                q, t = invert_cam_extrinsics(trans, quat)
                
                imgs_name_list = line[0].split(".")
                imgs_name = imgs_name_list[0] + imgs_name_list[1] + ".png"
    
                img_str += f"{int(count+1)} {q[0]} {q[1]} {q[2]} {q[3]} {t[0]} {t[1]} {t[2]} 1 {imgs_name}\n\n"
                count += 1

    save_path = os.path.join(colmap_imgs_path, 'images.txt')
    with open(save_path,'w') as of:
        of.write(img_str)
    
    # np.savetxt(save_path, img_str, delimiter=' ', fmt='%f')
    return img_str

def gen_database(database_file, cam_params, height, width, image_files, model=2):
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
    cam_poses_txt = args.cam_poses
    colmap_save_path = args.out_path
    image_path = args.images_path
    database_file_path = colmap_save_path.split("/")
    database_path = database_file_path[1:-2]

    database_file_path = os.path.join('/',*database_path, 'database.db')
    
    image_files = os.listdir(image_path)
    image_files = [img for img in image_files if img[-3:] == "png" ]
    image_files.sort()
    ts = [img.split(".")[0] for img in image_files]
    ts = [t[:10]+'.'+t[10:] for t in ts]
    # image_files = image_files[:num_cams]

    # create cameras file
    img = cv2.imread(os.path.join(image_path,image_files[0]))
    height, width, _ = img.shape

    imgs_txt = gen_imgs_file(cam_poses_txt, colmap_save_path, ts)
    
    cam_params = gen_cameras_file(height, width, colmap_save_path)
    
    fp = open(os.path.join(colmap_save_path,"points3D.txt"),'w')
    fp.close()
    
    gen_database(database_file_path, cam_params, height, width, image_files)

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--cam_poses', default="/home/harish/Documents/prof_ionnis_colmap/svin_2024_09_13_13_24_42.txt", help="path to the cam poses that will be used for initialization")
    parser.add_argument('--images_path', default="/home/harish/Documents/prof_ionnis_colmap/Images", help="path to the images that will be used by colmap for sparse reconstruction")
    parser.add_argument('--out_path', default="/home/harish/Documents/prof_ionnis_colmap/colmap/underwater/sparse/text", help="path to the folder where colmap will search for imgs.txt and cams.txt")
    
    args = parser.parse_args()
    main(args)