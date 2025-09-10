import sqlite3
import pickle
import os

from pathlib import Path
from shutil import copy2
from math import inf

import numpy as np

ROOT_PATH = "/home/luke/pamir"
PROJECT_PATH = f"{ROOT_PATH}/Combined_exhaustive"
DATABASE_PATH = f"{PROJECT_PATH}/database.db"
IMAGES_PATH = f"{PROJECT_PATH}/Images"
PICKLE_PATH = f"{PROJECT_PATH}/image_match_info.pkl"
PAMIR0_PATH = f"{ROOT_PATH}/Pamir0/Images"
PAMIR1_PATH = f"{ROOT_PATH}/Pamir1/Images"
PAMIR2_PATH = f"{ROOT_PATH}/Pamir2/Images"
INTERSEQ_PICKLE_PATH = f"{PROJECT_PATH}/images_by_inter_seq_feature_count.pkl"

# https://colmap.github.io/database.html#matches-and-two-view-geometries
def pair_id_to_image_ids(pair_id):
    image_id2 = pair_id % 2147483647
    image_id1 = int((pair_id - image_id2) / 2147483647)
    return image_id1, image_id2

def read_matches(database_path):
    #image_id_to_image_name, image_name_to_image_id = read_image_ids(database_path)
    image_match_info = {}

    with sqlite3.connect(database_path) as conn:
        cursor = conn.cursor()

        cursor.execute("SELECT pair_id, rows FROM two_view_geometries WHERE rows>0")

        # Define a chunk size to fetch rows in batches.
        # This is a tunable parameter; 5000 is a good starting point.
        chunk_size = 5000

        prev_image_id = -1
        while True:
            entries_batch = cursor.fetchmany(chunk_size)

            if not entries_batch:
                break

            for entry in entries_batch:
                pair_id, match_count = entry
                image_id1, image_id2 = pair_id_to_image_ids(pair_id)

                if image_id1 != prev_image_id:
                    prev_image_id = image_id1
                    print(f"Examining matches for {image_id1}")
                
                if image_id1 not in image_match_info:
                    image_match_info[image_id1] = []
                if image_id2 not in image_match_info:
                    image_match_info[image_id2] = []

                image_match_info[image_id1].append((image_id2, match_count))
                image_match_info[image_id2].append((image_id1, match_count))
    
    return image_match_info

def read_image_ids(database_path):
    image_id_to_image_name = {}
    image_name_to_image_id = {}

    with sqlite3.connect(database_path) as conn:
        cursor = conn.cursor()
        
        cursor.execute("SELECT image_id, name FROM images")
        
        rows = cursor.fetchall()

    for row in rows:
        image_id, image_name = row
        #print(f"{image_id}: {image_name}")
        image_id_to_image_name[image_id] = image_name
        image_name_to_image_id[image_name] = image_id
    
    return image_id_to_image_name, image_name_to_image_id

# image_match_info = read_matches(DATABASE_PATH)
# print("writing pickle")
# with open(PICKLE_PATH, "wb") as f:
#     pickle.dump(image_match_info, f)

def get_img_name_to_seq(folders):
    img_name_to_seq = {}

    for i in range(len(folders)):
        folder = folders[i]
        #print("Examining folder", folder)
        image_names = os.listdir(folder)
        for image_name in image_names:
            img_name_to_seq[image_name] = i

    return img_name_to_seq

def copy_with_dirs(src: str | Path, dst: str | Path) -> Path:
    src = Path(src)
    dst = Path(dst)  # full destination file path (including filename)
    dst.parent.mkdir(parents=True, exist_ok=True)  # create missing directories
    return Path(copy2(src, dst))  # returns the destination path


class Pipeline:
    def __init__(self):
        with open(PICKLE_PATH, "rb") as f:
            self.image_match_info = pickle.load(f)
        self.image_id_to_name, self.image_name_to_id = read_image_ids(DATABASE_PATH)
        self.image_name_to_seq = get_img_name_to_seq([PAMIR0_PATH, PAMIR1_PATH, PAMIR2_PATH])
        self.seqs = [0, 1, 2]
        self.seq_to_dir = [PAMIR0_PATH, PAMIR1_PATH, PAMIR2_PATH]
        
        self.image_names_by_seq = [None, None, None]
        self.read_image_seqs()

        with open(INTERSEQ_PICKLE_PATH, "rb") as f:
            self.images_by_inter_seq_feature_count = pickle.load(f)

    def read_image_seqs(self):
        for seq_num in self.seqs:
            path = self.seq_to_dir[seq_num]
            self.image_names_by_seq[seq_num] = sorted(os.listdir(path))

    def get_id(self, name):
        return self.image_name_to_id[name]
    
    def get_name(self, id):
        return self.image_id_to_name[id]

    def get_seq_by_id(self, image_id):
        return self.image_name_to_seq[self.get_name(image_id)]
    
    def get_seq_by_name(self, image_name):
        return self.image_name_to_seq[image_name]
    
    def sort_images(self):
        images_by_inter_seq_feature_count = []

        for id in self.image_match_info:
            my_seq = self.get_seq_by_id(id)
            matched_seqs = set([my_seq])
            inter_seq_feature_count = 0

            for match_id, feature_count in self.image_match_info[id]:
                #print(f"{id} matches to {match_id} with {feature_count} features")
                match_seq = self.get_seq_by_id(match_id)
                if match_seq != my_seq:
                    inter_seq_feature_count += feature_count
                    matched_seqs.add(match_seq)

            if len(matched_seqs) == len(self.seqs):
                #print(f"{id} has matches in all {len(self.seqs)} sequences, with a total of {inter_seq_feature_count} inter-sequential features")
                images_by_inter_seq_feature_count.append((id, inter_seq_feature_count))
        
        images_by_inter_seq_feature_count.sort(key=lambda x: x[1], reverse=True)

        self.images_by_inter_seq_feature_count = images_by_inter_seq_feature_count
        return images_by_inter_seq_feature_count

    def make_overlapping_seqs(self):
        best_img_id, best_img_match_count = self.images_by_inter_seq_feature_count[1000]
        best_img_name = self.get_name(best_img_id)
        best_img_seq = self.get_seq_by_id(best_img_id)
        print(f"The best image is {best_img_id}, with name {best_img_name} in seq {best_img_seq}.")

        overlapping_seq = self.make_overlapping_seq(best_img_id)
        for img_id in overlapping_seq:
            #print(img_id)
            seq = self.get_seq_by_id(img_id)
            name = self.get_name(img_id)
            path = f"{IMAGES_PATH}/{name}"
            new_path = f"{PROJECT_PATH}/matched/{seq}/{name}"
            copy_with_dirs(path, new_path)
            

    def make_overlapping_seq(self, start_id, max_length=500):
        base_id = start_id
        base_seq = self.get_seq_by_id(base_id)
        base_name = self.get_name(base_id)
        base_index_in_own_seq = self.image_names_by_seq[base_seq].index(base_name)
        print(f"Image is at index {base_index_in_own_seq}")

        # print(self.image_names_by_seq[base_seq][base_index_in_own_seq])
        # print(self.image_names_by_seq[base_seq][base_index_in_own_seq+1])
        # print(self.image_names_by_seq[base_seq][base_index_in_own_seq+2])

        # return
        
        total_length = 0

        steps_forward = 0
        steps_backward = 1
        curr_index = base_index_in_own_seq
        curr_direction = 1
        overlapping_images = set()

        steps_since_last_forward = 0
        steps_since_last_backward = 0

        while total_length < max_length:
            if curr_direction == 1:
                if base_index_in_own_seq + steps_forward < len(self.image_names_by_seq[base_seq]):
                    curr_index = base_index_in_own_seq + steps_forward
                    steps_forward += 1
                else:
                    steps_forward = -1
            elif curr_direction == -1:
                if base_index_in_own_seq - steps_backward >= 0:
                    curr_index = base_index_in_own_seq - steps_backward
                    steps_backward += 1
                else:
                    steps_backward = -1
            
            print(f"Index is {curr_index}")

            curr_img_name = self.image_names_by_seq[base_seq][curr_index]
            curr_img_id = self.get_id(curr_img_name)

            matched_seqs = set([base_seq])
            matched_imgs = set()

            for match_id, feature_count in self.image_match_info[curr_img_id]:
                match_seq = self.get_seq_by_id(match_id)
                if match_seq != base_seq:
                    #print(f"{match_id} ({self.get_name(match_id)}) is an image in another sequence that matches {curr_img_id} ({curr_img_name})")
                    matched_seqs.add(match_seq)
                    matched_imgs.add(match_id)

            if len(matched_seqs) == len(self.seqs):
                print(f"All seqs were found for image {curr_img_id}, at index {curr_index}.")
                overlapping_images = overlapping_images.union(matched_imgs)
                overlapping_images.add(curr_img_id)
                if curr_direction == 1:
                    steps_since_last_forward = 0
                elif curr_direction == -1:
                    steps_since_last_backward = 0
            else:
                #print(f"Matches for {curr_img_id} were found in {len(matched_seqs)} seqs total.")
                if curr_direction == 1:
                    # Meaning the direction that got us here was actually forward
                    #steps_forward = -1
                    steps_since_last_forward += 1
                    if steps_since_last_forward > 1:
                        print("The forward chain dies here.")
                        steps_forward = -1
                elif curr_direction == -1:
                    steps_since_last_backward += 1
                    if steps_since_last_backward > 1:
                        print("The backward chain dies here.")
                        steps_backward = -1
            
            if steps_backward and steps_forward == -1:
                break
            elif steps_backward == -1:
                curr_direction = 1
            elif steps_forward == -1:
                curr_direction = -1
            else:
                curr_direction *= -1
        
        print(f"Overlapping images size: {len(overlapping_images)}")
        return overlapping_images

    def get_corresponding_points(self, base_path):
        image_name_to_colmap_center = {}
        image_name_to_svin_center = {}

        with open(f"{base_path}/sparse/text/images.txt") as f:
            data_line = True

            for line in f:
                line = line.rstrip()
                if line.startswith("#"):
                    continue

                if data_line:
                    image_id, qw, qx, qy, qz, tx, ty, tz, camera_id, image_name = line.split(" ")
                    tx = float(tx)
                    ty = float(ty)
                    tz = float(tz)

                    seq = self.get_seq_by_name(image_name)
                    image_name_to_colmap_center[image_name] = [tx, ty, tz]

                data_line = not data_line
        
        with open(f"{base_path}/svin_noninv.txt") as f:
            for line in f:
                if line.startswith("#"):
                    continue
                
                line = line.rstrip()
                #timestamp tx ty tz qx qy qz qw
                timestamp, tx, ty, tz, qx, qy, qz, qw = line.split(" ")
                image_name = f"{timestamp.replace(".", "")}.png"
                tx = float(tx)
                ty = float(ty)
                tz = float(tz)

                image_name_to_svin_center[image_name] = [tx, ty, tz]

        matched_cameras = []
        image_names_by_seq = [[], [], []]
        for image_name in sorted(image_name_to_colmap_center.keys()):
            seq = self.get_seq_by_name(image_name)
            image_names_by_seq[seq].append(image_name)

        for seq in image_names_by_seq:
            source = np.zeros((len(seq), 3))
            dest = np.zeros((len(seq), 3))
  
            for i in range(len(seq)):
                source[i] = image_name_to_svin_center[seq[i]]
                dest[i] = image_name_to_colmap_center[seq[i]]
            
            matched_cameras.append((source, dest))
        
        return matched_cameras

    def split_and_plot(self, base_path):
        data_line = True
        ply_paths = [f"{base_path}/seq_{i}.ply" for i in self.seqs]
        ply_lines = [[] for i in self.seqs]

        for i in self.seqs:
            ply_lines[i].append('ply\n')
            ply_lines[i].append('format ascii 1.0\n')
            ply_lines[i].append('comment Right-Handed System\n')
            ply_lines[i].append(f'element vertex {0}\n')
            ply_lines[i].append('property float x\n')
            ply_lines[i].append('property float y\n')
            ply_lines[i].append('property float z\n')
            ply_lines[i].append('property uchar red\n')
            ply_lines[i].append('property uchar green\n')
            ply_lines[i].append('property uchar blue\n')
            ply_lines[i].append('end_header\n')

        with open(f"{base_path}/sparse/text/images.txt") as f:
            for line in f:
                line = line.rstrip()
                if line.startswith("#"):
                    continue

                if data_line:
                    image_id, qw, qx, qy, qz, tx, ty, tz, camera_id, image_name = line.split(" ")
                    tx = float(tx)
                    ty = float(ty)
                    tz = float(tz)

                    seq = self.get_seq_by_name(image_name)
                    ply_lines[seq].append(f"{tx} {ty} {tz} 255 0 0\n")

                data_line = not data_line

        for i in self.seqs:
            ply_lines[i][3] = f'element vertex {len(ply_lines[i])-11}\n'
            with open(ply_paths[i], "w+") as f:
                for line in ply_lines[i]:
                    f.write(line)

    def get_poses(lines):
        poses = []
        for line in lines:
            if line[0] == "#":
                continue
            poses.append([float(num) for num in line.split(" ")[1:-1]])
        return poses

def kabsch_umeyama(P, Q):
    """
    Finds the optimal rigid transformation (rotation and translation)
    that aligns two sets of corresponding points P and Q using the
    Kabsch-Umeyama algorithm.

    Args:
        P (np.ndarray): A NxD matrix of N points in D dimensions.
        Q (np.ndarray): A NxD matrix of N corresponding points in D dimensions.

    Returns:
        tuple: A tuple containing:
            - R (np.ndarray): The DxD optimal rotation matrix.
            - t (np.ndarray): The Dx1 optimal translation vector.
            - rmsd (float): The Root Mean Square Deviation after alignment.
    """
    # Ensure the input matrices have the same shape
    assert P.shape == Q.shape, "Input point sets must have the same shape"
    
    N, D = P.shape

    # 1. Center the point sets
    centroid_P = np.mean(P, axis=0)
    centroid_Q = np.mean(Q, axis=0)
    P_centered = P - centroid_P
    Q_centered = Q - centroid_Q

    # 2. Compute the covariance matrix H
    # H = (P_centered^T) * Q_centered
    H = P_centered.T @ Q_centered

    # 3. Perform Singular Value Decomposition (SVD)
    U, S, Vt = np.linalg.svd(H)
    
    # Transpose of V is returned by np.linalg.svd
    V = Vt.T

    # 4. Calculate the optimal rotation matrix R
    R = V @ U.T

    # 5. Handle reflections (the Umeyama correction)
    # If the determinant is -1, it's a reflection, not a rotation.
    # We flip the sign of the column of V corresponding to the smallest singular value.
    if np.linalg.det(R) < 0:
        # The singular values in S are sorted in descending order.
        # So, the last column of V corresponds to the smallest singular value.
        V[:, -1] *= -1
        R = V @ U.T

    # 6. Calculate the optimal translation vector t
    t = centroid_Q - R @ centroid_P
    
    # 7. Apply the transformation and calculate RMSD
    P_aligned = (R @ P.T).T + t
    rmsd = np.sqrt(np.mean(np.sum((P_aligned - Q)**2, axis=1)))

    return R, t, rmsd

pipeline = Pipeline()
# pipeline.make_overlapping_seqs() # call this to get the overlapping sequences
# pipeline.sort_images()
# print(len(pipeline.images_by_inter_seq_feature_count))
# with open(INTERSEQ_PICKLE_PATH, "wb") as f:
#     pickle.dump(pipeline.images_by_inter_seq_feature_count, f)

#def rank_images_by_match_count(image_match_info):

#pipeline.split_and_plot("/home/luke/pamir/matchmania/Combined")
print("KABACH RESULT")
matched_cameras = pipeline.get_corresponding_points("/home/luke/pamir/matchmania/Combined")
result = kabsch_umeyama(matched_cameras[0][0], matched_cameras[0][1])
print(result)
#print(len(matched_cameras[0][0]))
#transform = estimate_similarity_transformation(matched_cameras[0][0], matched_cameras[0][0])
# def rigid_transform(points: NDArray[Any], transform: NDArray[Any]) -> NDArray[Any]:
#     """ Apply's a rigid transform to a collection of 3D points.

#     Parameters:
#     points: Array of 3D points of size [N x 3]
#     transform: rigid transform to be pre-multiplied of size [4x4]

#     Returns:
#     The transformed 3D points.
#     """
#     N = points.shape[0]
#     homog_coords = np.concatenate(points, np.ones_like(points[:,0:1])).reshape(N,4,1)
#     transform = np.tile(transform.reshape(1,4,4), (N,1,1))

#     return np.matmul(transform, homog_coords)[:,:3,0]

# def read_point_cloud(point_cloud_file: str) -> NDArray[np.float32]:
#     """Reads a point cloud from a file.

#     Parameters:
#     point_cloud_file: Input point cloud file.

#     Returns:
#     The point cloud as an NDArray stored in the given file.
#     """
#     cloud = o3d.io.read_point_cloud(point_cloud_file)
#     return np.array(cloud.points, dtype=np.float32)

print("PROCRUSTES RESULT")
from procrustes import orthogonal
from procrustes.utils import _translate_array
result = orthogonal(matched_cameras[0][0], matched_cameras[0][1], scale=True, translate=True)
print(result.t.T)

# accessing the translation matrix
trans_array_a, centroid = _translate_array(matched_cameras[0][0], matched_cameras[0][1])
print(centroid)

print("PROCRUSTES SCIPY")
from procrustesl import procrustes
procrustes(matched_cameras[0][0], matched_cameras[0][1])

# https://zpl.fi/aligning-point-patterns-with-kabsch-umeyama-algorithm/
print("\nFrom CPL")
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

svin_centers = matched_cameras[2][0]
colmap_centers = matched_cameras[2][1]

# from homograph_pc import *
from homograph_pc import *

write_point_cloud_np("/home/luke/pamir/Combined_exhaustive/matched/colmap_centers_orig.ply", colmap_centers)
write_point_cloud_np("/home/luke/pamir/Combined_exhaustive/matched/svin_centers_orig.ply", svin_centers)

A = colmap_centers[:]
B = svin_centers[:]
R, c, t = kabsch_umeyama(A, B)
B = np.array([t + c * R @ b for b in B])

# print(R, c, t)
# M = np.empty((4, 4))
# M[:3, :3] = R*c
# M[:3, 3] = t
# M[3, :] = [0, 0, 0, 1]
# print(M)

write_point_cloud_np("/home/luke/pamir/Combined_exhaustive/matched/colmap_centers.ply", A)
write_point_cloud_np("/home/luke/pamir/Combined_exhaustive/matched/svin_centers.ply", B)

# # M = np.eye(4) * 1.05
# # M[3][3] = 1

# points, colors = read_point_cloud("/home/luke/pamir/Combined_exhaustive/matched/svin_0.ply")
# print(points[0])
# #transformed_points = apply_homography(points, M)
# transformed_points = np.array([t + c * R @ b for b in points])

# write_point_cloud_np("/home/luke/pamir/Combined_exhaustive/matched/svin_0_trans.ply", transformed_points, colors)
