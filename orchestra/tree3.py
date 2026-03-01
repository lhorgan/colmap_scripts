import numpy as np

from homograph_pc import *
from rotate_svin_traj import *
from plot_cams import *

def get_corresponding_points(svin_path, svin_from_colmap_path):
        image_name_to_colmap_center = {}
        image_name_to_svin_center = {}

        # Cam poses from COLMAP must be inverted!
        with open(svin_from_colmap_path) as f:
            for line in f:
                if line.startswith("#"):
                        continue
                    
                line = line.rstrip()
                #timestamp tx ty tz qx qy qz qw
                timestamp, tx, ty, tz, qx, qy, qz, qw = line.split(" ")
                image_name = f"{timestamp.replace('.', '')}.png"
                tx = float(tx)
                ty = float(ty)
                tz = float(tz)

                image_name_to_colmap_center[image_name] = [tx, ty, tz]

        # SVIN poses must not be inverted    
        with open(svin_path) as f:
            for line in f:
                if line.startswith("#"):
                    continue
                
                line = line.rstrip()
                #timestamp tx ty tz qx qy qz qw
                timestamp, tx, ty, tz, qx, qy, qz, qw = line.split(" ")
                image_name = f"{timestamp.replace('.', '')}.png"
                tx = float(tx)
                ty = float(ty)
                tz = float(tz)

                image_name_to_svin_center[image_name] = [tx, ty, tz]

        svin_points = []
        colmap_points = []
        for image_name in image_name_to_colmap_center:
             if image_name in image_name_to_svin_center:
                #print(image_name, image_name_to_svin_center[image_name], image_name_to_colmap_center[image_name])
                svin_points.append(image_name_to_svin_center[image_name])
                colmap_points.append(image_name_to_colmap_center[image_name])
        
        svin_points = np.array(svin_points)
        colmap_points = np.array(colmap_points)

        print(len(svin_points), len(colmap_points))

        return svin_points, colmap_points

def plot_trajectory(input_file_path, output_file_path):
    with open(input_file_path) as f:
        lines = f.readlines()

    with open(output_file_path, 'w') as f:
        # write header meta-data
        f.write('ply\n')
        f.write('format ascii 1.0\n')
        f.write('comment Right-Handed System\n')
        f.write(f'element vertex {len(lines)-1}\n')
        f.write('property float x\n')
        f.write('property float y\n')
        f.write('property float z\n')
        f.write('property uchar red\n')
        f.write('property uchar green\n')
        f.write('property uchar blue\n')
        f.write('end_header\n')

        for line in lines[1:]:
            tx, ty, tz = [float(t) for t in line.split(" ")[1:4]]
            f.write(f"{tx} {ty} {tz} 255 0 0\n")

def kabsch_umeyama(A, B):
    assert A.shape == B.shape
    n, m = A.shape

    EA = np.mean(A, axis=0)
    EB = np.mean(B, axis=0)
    VarA = np.mean(np.linalg.norm(A - EA, axis=1) ** 2)

    H = ((A - EA).T @ (B - EB)) / n
    U, D, VT = np.linalg.svd(H)
    d = np.sign(np.linalg.det(U) * np.linalg.det(VT))
    S = np.diag([1] * (m - 1) + [d])

    R = U @ S @ VT
    c = VarA / np.trace(np.diag(D) @ S)
    t = EA - c * R @ EB

    return R, c, t

def get_homography_matrix(A, B):
    R, c, t = kabsch_umeyama(A, B)
    M = np.empty((4, 4))
    M[:3, :3] = R*c
    M[:3, 3] = t
    M[3, :] = [0, 0, 0, 1]
    return M

def align_point_cloud(svin_centers, colmap_centers, ship_point_cloud_file_path, ship_output_path, cam_output_path):
    A = svin_centers
    B = colmap_centers 

    # B gets aligned to A
    M = get_homography_matrix(A, B)

    ship_points, ship_colors = read_point_cloud(ship_point_cloud_file_path)
    trans_ship_points = apply_homography(ship_points, M)
    trans_colmap_centers = apply_homography(B, M)
    write_point_cloud_np(ship_output_path, trans_ship_points, ship_colors)
    write_point_cloud_np(cam_output_path, trans_colmap_centers)
    return M

def hang_models(data_path, scene):
    aligned_cubes_path = "/mnt/disk_1_ssd/luke/blub/mah/aligned_spheres"
    aligned_cams_path = "/mnt/disk_1_ssd/luke/blub/mah/aligned_cams"
    aligned_poses_path = "/mnt/disk_1_ssd/luke/blub/mah/aligned_poses"
    aligned_poses_plys_path = "/mnt/disk_1_ssd/luke/blub/mah/aligned_poses_plys"

    scaffold_path = f"/mnt/disk_1_ssd/luke/blub/svin_raw/Center.txt"

    sparse_dir = f"{data_path}/{scene}/sparse"
    models = os.listdir(sparse_dir)
    for model in models:
        model_dir = f"{sparse_dir}/{model}"
        svin_from_colmap_path = f"{model_dir}/svin_from_colmap_inv.txt" # This one must be inverted!
        svin_centers, colmap_centers = get_corresponding_points(scaffold_path, svin_from_colmap_path)
        if len(svin_centers) > 30:
            M = align_point_cloud(svin_centers, colmap_centers, f"{model_dir}/{scene}-{model}.ply", f"{aligned_cubes_path}/{scene}-{model}.ply", f"{aligned_cams_path}/{scene}-{model}.ply")
            #rotate_svin_traj(svin_from_colmap_path, f"{aligned_cams_path}/{scene}-{model}_traj.ply", M)
            rotate_svin_traj(svin_from_colmap_path, f"{aligned_poses_path}/{scene}-{model}.txt", M)
            plot_cameras(f"{aligned_poses_path}/{scene}-{model}.txt", 0.00008, f"{aligned_poses_plys_path}/{scene}-{model}.ply")
        else:
            print("Skipping, not enough points")

import os

def hang_all():
    data_path = "/mnt/disk_1_ssd/luke/blub/spheres"
    scenes = os.listdir(data_path)
    for scene in scenes:
        #try:
            print("Hanging ", scene)
            hang_models(data_path, scene)
        # except:
        #     print("Could not hang ", scene)
        # break

hang_all()