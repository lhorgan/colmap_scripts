import sqlite3
import pickle
import os

from pathlib import Path
from shutil import copy2
from math import inf

import numpy as np

ROOT_PATH = "/home/luke/Documents/Ship"
PROJECT_PATH = f"{ROOT_PATH}/Combined"
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

def read_image_names_from_dirs(dirs):
    image_names = []
    for path in dirs:
        image_names += os.listdir(path)
    return set(image_names)

def read_matches(database_path):
    image_match_info = {}
    images_in_dirs = read_image_names_from_dirs([PAMIR0_PATH, PAMIR1_PATH, PAMIR2_PATH])
    image_id_to_image_name, _ = read_image_ids(database_path)

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
                
                image_name1 = image_id_to_image_name[image_id1]
                image_name2 = image_id_to_image_name[image_id2]

                if image_name1 not in images_in_dirs or image_name2 not in images_in_dirs:
                    #print("Skipping because match is not under consideration.")
                    continue

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

        # with open(INTERSEQ_PICKLE_PATH, "rb") as f:
        #     self.images_by_inter_seq_feature_count = pickle.load(f)

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

    # 0
    # 30
    # 90, same as 0 but better
    # 1500
    # 1900, excellent
    # 2500
    # 832, excellent, pairs with 90

    def make_overlapping_seqs(self):
        index = 0
        for id, count in self.images_by_inter_seq_feature_count:
            name = self.image_id_to_name[id]
            if name == "1737109004420952666.png":
                break
            index += 1
                
        print(f"looking at index {index}")
        #index = 90

        best_img_id, best_img_match_count = self.images_by_inter_seq_feature_count[index]
        best_img_name = self.get_name(best_img_id)
        best_img_seq = self.get_seq_by_id(best_img_id)
        print(f"The best image is {best_img_id}, with name {best_img_name} in seq {best_img_seq}.")

        overlapping_seq = self.make_overlapping_seq(best_img_id)
        for img_id in overlapping_seq:
            #print(img_id)
            seq = self.get_seq_by_id(img_id)
            name = self.get_name(img_id)
            path = f"{IMAGES_PATH}/{name}"
            new_path = f"{PROJECT_PATH}/matched_913/{seq}/{name}"
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

        # with open(f"{base_path}/sparse/text/images.txt") as f:
        #     data_line = True

        #     for line in f:
        #         line = line.rstrip()
        #         if line.startswith("#"):
        #             continue

        #         if data_line:
        #             image_id, qw, qx, qy, qz, tx, ty, tz, camera_id, image_name = line.split(" ")
        #             tx = float(tx)
        #             ty = float(ty)
        #             tz = float(tz)

        #             seq = self.get_seq_by_name(image_name)
        #             image_name_to_colmap_center[image_name] = [tx, ty, tz]

        #         data_line = not data_line
        with open(f"{base_path}/svin_from_colmap_inv.txt") as f:
            for line in f:
                if line.startswith("#"):
                        continue
                    
                line = line.rstrip()
                #timestamp tx ty tz qx qy qz qw
                timestamp, tx, ty, tz, qx, qy, qz, qw = line.split(" ")
                #image_name = f"{timestamp.replace(".", "", 1)}" # this is messed up because I screwed up making the svin file
                image_name = f"{timestamp.replace(".", "", 1)}.png"
                tx = float(tx)
                ty = float(ty)
                tz = float(tz)

                image_name_to_colmap_center[image_name] = [tx, ty, tz]

        
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

# image_match_info = read_matches(DATABASE_PATH)
# print("writing pickle")
# with open(PICKLE_PATH, "wb") as f:
#     pickle.dump(image_match_info, f)

from mhelp import *
from homograph_pc import *

pipeline = Pipeline()
#pipeline.sort_images()
#pipeline.make_overlapping_seqs() # call this to get the overlapping sequences

# matched_cameras = pipeline.get_corresponding_points(f"/home/luke/Documents/Ship/{"Front"}/combo")

# def transform_icp():
#     area = "Front"

#     full_plys = ["/home/luke/pamir/Pamir0_incref/pamir0.ply", "/home/luke/pamir/Pamir1_incref/pamir1.ply", "/home/luke/pamir/Pamir2_incref/pamir2.ply"]
#     seq_plys = [f"/home/luke/Documents/Ship/{area}/seq{i}/seq{i}.ply" for i in range(3)]
#     seqs_from_colmap = f"/home/luke/Documents/Ship/{area}/combo/sparse.ply"
#     target_points, _ = read_point_cloud(seqs_from_colmap)

#     for i in range(3):
#         print(f"Transforming pamir{i}")

#         svin_centers = matched_cameras[i][0]
#         colmap_centers = matched_cameras[i][1]

#         A = colmap_centers
#         B = svin_centers
        
#         M1 = get_homography_matrix(A, B)

#         print(f"M1 for pamir{i}:\n{M1}")

#         points, colors = read_point_cloud(seq_plys[i])
        
#         trans_points = apply_homography(points, M1)

#         write_point_cloud_np(f"/home/luke/Documents/Ship/{area}/point_clouds/seq{i}_homography_only.ply", trans_points, colors)

#         #write_point_cloud_np(f"/home/luke/pamir/transformed_pcs/pamir{i}.ply", trans_points, colors)

#         aligned_pc_icp, M2 = align_icp(target_points, trans_points)

#         print(M2)

#         write_point_cloud_np(f"/home/luke/Documents/Ship/{area}/point_clouds/seq{i}_icp.ply", aligned_pc_icp.points, colors)

#         full_points, full_colors = read_point_cloud(full_plys[i])

#         M1 @ M2

#         full_points = apply_homography(full_points, M1)
#         full_points = apply_homography(full_points, M2)
#         write_point_cloud_np(f"/home/luke/Documents/Ship/{area}/point_clouds/pamir{i}_h_p_icp.ply", full_points, full_colors)

from gem import *
from gem2 import *

def transform_full():
    BACK = 0
    FRONT = 1

    seq_plys = [
        [None, "/home/luke/Documents/Ship/Back/seq1/seq1.ply", "/home/luke/Documents/Ship/Back/seq2/seq2.ply"],
        [None, "/home/luke/Documents/Ship/Front/seq1/seq1.ply", "/home/luke/Documents/Ship/Front/seq2/seq2.ply"]
    ]

    seqs_from_colmap = [
        f"/home/luke/Documents/Ship/Back/combo/sparse.ply",
        f"/home/luke/Documents/Ship/Front/combo/sparse.ply"
    ]

    matched_cameras_back = pipeline.get_corresponding_points(f"/home/luke/Documents/Ship/Back/combo")
    matched_cameras_front = pipeline.get_corresponding_points(f"/home/luke/Documents/Ship/Front/combo")
    matched_cameras = [matched_cameras_back, matched_cameras_front]

    areas = ["Back", "Front"]

    transformations = [
        [None, None, None],
        [None, None, None]
    ]

    for i in range(len(areas)):
        target_points, _ = read_point_cloud(seqs_from_colmap[i])

        for j in range(3):
            if seq_plys[i][j] is None:
                continue

            print(f"Transforming pamir{j}")

            svin_centers = matched_cameras[i][j][0]
            colmap_centers = matched_cameras[i][j][1]

            A = colmap_centers
            B = svin_centers
            
            M1 = get_homography_matrix(A, B)
            print(f"M1 for pamir{j}:\n{M1}")
            points, colors = read_point_cloud(seq_plys[i][j])
            trans_points = apply_homography(points, M1)
            aligned_pc_icp, M2 = align_icp(target_points, trans_points)

            transformations[i][j] = M2 @ M1

    final_transforms = [None, None]
    final_quats = [None, None]

    for i in range(len(areas)):
        pamir_1_to_colmap = transformations[i][1]
        colmap_to_pamir1 = np.linalg.inv(pamir_1_to_colmap)
        pamir_2_to_colmap = transformations[i][2]
        pamir_2_to_pamir1 = colmap_to_pamir1 @ pamir_2_to_colmap
        final_transforms[i] = pamir_2_to_pamir1

    for i in range(len(final_transforms)):
        trans, quat = matrix_to_quat_trans(final_transforms[i])
        final_quats[i] = (trans, quat)
    
    svin_centers_pamir2_back = matched_cameras[BACK][2][0] # [1] in the last index is the COLMAP centers
    svin_centers_pamir2_front = matched_cameras[FRONT][2][0]

    line_points = [geo_mean(svin_centers_pamir2_back), geo_mean(svin_centers_pamir2_front)]
    line_start, line_dir = define_line_from_points(line_points[0], line_points[1])

    # tx ty tz qx qy qx qw
    comment = None
    pamir2_poses = []
    with open("/home/luke/pamir/Pamir2/Pamir2_transformed.txt") as f:
        for line in f:
            if line.startswith("#"):
                comment = line
                continue
            #pose = [float(x) for x in (line.split(" ")[1:])]
            pamir2_poses.append(line)
    
    pamir2_poses = np.array(pamir2_poses)    
    
    start_trans, start_quat = final_quats[0]
    end_trans, end_quat = final_quats[1]

    with open("/home/luke/pamir/Pamir2/Pamir2_in_Pamir1_miraculously.txt", "w+") as f:
        f.write(comment)
        for line in pamir2_poses:
            pose = [float(x) for x in (line.split(" ")[1:])]
            timestamp = line.split(" ")[0]

            point = pose[:3]
            quat = pose[3:]

            point_prime = project_point_onto_line(point, line_start, line_dir)
            t = get_line_parameter(point_prime, line_points[0], line_points[1])
            print("t is", t)
            curr_trans, curr_quat = interpolate_transform(start_trans, start_quat, end_trans,  end_quat, t)
            print("trans", curr_trans, "quat", curr_quat.shape)
            #new_point, new_quat = apply_transform_with_matrices(point, quat, np.array([0, 0, 0]), np.array([0, 0, 0, 1]))
            new_point, new_quat = apply_transform_with_matrices(point, quat, start_trans, start_quat)
            f.write(f"{timestamp} {new_point[0]} {new_point[1]} {new_point[2]} {new_quat[0]} {new_quat[1]} {new_quat[2]} {new_quat[3]}\n")

transform_full()