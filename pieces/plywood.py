import open3d as o3d
import numpy as np
#import itertools
import copy
import shutil

from pathlib import Path

def copy_img(src_path, dst_path):
    Path(dst_path).parent.mkdir(parents=True, exist_ok=True)
    shutil.copy(src_path, dst_path)

def read_point_cloud(file_path):
    """Read a point cloud from file"""
    return o3d.io.read_point_cloud(file_path)

def write_point_cloud(point_cloud, file_path):
    """Write the point cloud to the file path specified"""
    o3d.io.write_point_cloud(file_path, point_cloud)
# def write_point_cloud(filename, points, colors=None):
#     cloud = o3d.geometry.PointCloud()
#     cloud.points = o3d.utility.Vector3dVector(points)
#     if colors is not None:
#         cloud.colors = o3d.utility.Vector3dVector(colors)
#     o3d.io.write_point_cloud(filename, cloud)

def parse_key(key):
    x, y, z = [int(k) for k in key.split("_")[1:]]
    return x, y, z

def make_key(x, y, z):
    return f"bin_{x}_{y}_{z}"

class PCSplitter():
    def __init__(self, pcd_path, obs_path):
        self.pcd_path = pcd_path
        self.pcd = read_point_cloud(pcd_path)
        self.obs_path = obs_path
        #self.align_bb()
        self.points = np.asarray(self.pcd.points)

    def id_points(self):
        pcd_tree = o3d.geometry.KDTreeFlann(self.pcd)

        self.keyframes_by_point_id = {}

        with open(self.obs_path) as f:
            for line in f:
                if line.startswith("#"):
                    continue
                
                line = line.strip()

                landmark_id, coords, keyframes = line.split("[")
                landmark_id = landmark_id.replace(",", "")
                landmark_id = int(landmark_id)

                coords = coords[:-3]
                coords = coords.split(",")
                coords = [float(l) for l in coords]

                keyframes = keyframes.replace("]", "")
                keyframes = keyframes.split(",")
                keyframes = [int(k) for k in keyframes]

                k, idx, dist = pcd_tree.search_knn_vector_3d(coords, 1)
                #print(f"The point closest is at {idx[0]} with distance {dist[0]}")
                #print(f"KEYFRAMES FOR {coords}", keyframes)
                idx = idx[0]
                
                if idx not in self.keyframes_by_point_id:
                    self.keyframes_by_point_id[idx] = set()
                self.keyframes_by_point_id[idx].update(keyframes)

    def get_keyframes_by_point(self, x, y, z):
        pcd_tree = o3d.geometry.KDTreeFlann(self.pcd)
        coords = [x, y, z]
        k, idx, dist = pcd_tree.search_knn_vector_3d(coords, 1)
        print("DIST IS ", dist)
        idx = idx[0]
        keyframes = self.keyframes_by_point_id[idx]
        print(self.points[idx])
        print("ASSOCIATED KEYFRAMES ARE ", keyframes)
        for keyframe_id in keyframes:
            print(self.keyframe_id_to_timestamp[keyframe_id])


    # Map keyframe ids to timestamps
    def build_timestamp_database(self, keyframe_path):
        self.keyframe_id_to_timestamp = {}
        with open(keyframe_path) as f:
            for line in f:
                if line.startswith("#"):
                    continue
                line = line.split(",")
                id = int(line[0])
                timestamp = line[1]
                self.keyframe_id_to_timestamp[id] = timestamp

    def align_bb(self):
        # Get original OBB
        obb_original = self.pcd.get_oriented_bounding_box()
        original_extent = obb_original.extent

        pcd_rotated = copy.deepcopy(self.pcd)
        
        # Rotate and center
        pcd_rotated.rotate(obb_original.R.T, center=(0, 0, 0))
        pcd_rotated.translate(-pcd_rotated.get_center())
        
        # Check the new AABB
        aabb = self.pcd.get_axis_aligned_bounding_box()
        new_extent = aabb.get_extent()
        
        print(f"Original OBB extent: {original_extent}")
        print(f"Aligned AABB extent: {new_extent}")
        print(f"Difference: {np.abs(original_extent - new_extent)}")

        return pcd_rotated

    def get_bounds(self, pcd):
        bb = pcd.get_axis_aligned_bounding_box()
        #print(bb)
        #print(self.pcd.get_oriented_bounding_box())

        min_x, min_y, min_z = bb.min_bound
        max_x, max_y, max_z = bb.max_bound
        return min_x, max_x, min_y, max_y, min_z, max_z
    
    def inds_to_key(self, x, y, z):
        return f"bin_{x}_{y}_{z}"

    def bin_points(self, bin_count, overlap_thresh=0.1):
        rotated_pcd = self.align_bb()
        points = np.asarray(rotated_pcd.points)

        n = bin_count
        min_x, max_x, min_y, max_y, min_z, max_z = self.get_bounds(rotated_pcd)
        lx = max_x - min_x
        ly = max_y - min_y
        lz = max_z - min_z

        nx = ((n * lx**2) / (ly * lz))**(1/3)
        lb = lx / nx
        print("Length of a box", lb)
        print(lx / lb)
        print(ly / lb)
        print(lz / lb)

        bins = {}
        for idx, (x, y, z) in enumerate(points):
            bin_x = (x - min_x) / lb
            bin_y = (y - min_y) / lb
            bin_z = (z - min_z) / lb
            bin = [bin_x, bin_y, bin_z]
            
            for i in range(3):
                bin_i_int = int(bin[i])
                bin_i_dec = bin[i] - bin_i_int
                if bin_i_dec < overlap_thresh and bin[i] - 1 >= 0:
                    bin_int = [int(b) for b in bin]
                    bin_int[i] -= 1
                    bin_key = self.inds_to_key(*bin_int)
                    if bin_key not in bins:
                        bins[bin_key] = set()
                    bins[bin_key].add(idx)
            
            bin_key = self.inds_to_key(int(bin_x), int(bin_y), int(bin_z))
            if bin_key not in bins:
                bins[bin_key] = set()
            bins[bin_key].add(idx)
        
        lens = np.zeros(len(bins))
        for i, key in enumerate(bins):
            lens[i] = len(bins[key])
        mean_len = np.mean(lens)
        std_dev = np.std(lens)
        print(f"Mean: {mean_len}, Std Dev: {std_dev}")

        for i, key in enumerate(bins):
            if len(bins[key]) < mean_len / 2:
                #print(f"Bin {key} has {len(bins[key])} points and is GARBAGE")
                pass
        
        total_len = 0
        for key in bins:
            #print(key, len(bins[key]))
            total_len += len(bins[key])
        
        self.bins = bins

        print(f"We have {len(self.bins)} bins.")
        return bins

    def write_bins(self, img_input_dir, output_dir):
        rotated_pcd = self.align_bb()
        points = np.asarray(rotated_pcd.points)

        lens = np.zeros(len(self.bins))
        for i, key in enumerate(self.bins):
            lens[i] = len(self.bins[key])
        mean_len = np.mean(lens)
        std_dev = np.std(lens)
        print(f"Mean: {mean_len}, Std Dev: {std_dev}")

        for bin_key in self.bins:
            #print(bin_key)
            if bin_key != "bin_10_1_0":
                continue

            idxs = self.bins[bin_key]
            # if len(idxs) < mean_len / 4:
            #     continue

            print("Writing bin ", bin_key)

            pcd = o3d.geometry.PointCloud()
            pcd.points = o3d.utility.Vector3dVector(np.array(self.points[list(idxs)]))
            
            keyframes_already_copied = {}
            for idx in idxs:
                keyframes = self.keyframes_by_point_id[idx]
                for keyframe_id in keyframes:
                    # if keyframe_id in keyframes_already_copied:
                    #     continue
                    
                    if keyframe_id not in keyframes_already_copied:
                        keyframes_already_copied[keyframe_id] = 0
                    keyframes_already_copied[keyframe_id] += 1

                    # if keyframe_id in self.keyframe_id_to_timestamp:
                    #     timestamp = self.keyframe_id_to_timestamp[keyframe_id]
                    #     image_name = timestamp.replace(".", "").strip()
                    #     print(f"WE MUST RETRIEVE KEYFRAME {keyframe_id} => {timestamp} for point {idx} at {self.points[idx]}")
                    #     try:
                    #         copy_img(f"{img_input_dir}/{image_name}.png", f"{output_dir}/{bin_key}/Images/{image_name}.png")
                    #     except FileNotFoundError:
                    #         pass
                    #         #print("There is no keyframe ", {image_name})
                    # else:
                    #     #print(f"We are missing a mapping for keyframe id ", keyframe_id)
                    #     pass
            
            for keyframe_id in keyframes_already_copied:
                votes_for_keyframe = keyframes_already_copied[keyframe_id]
                print(votes_for_keyframe)
                if votes_for_keyframe > 200:
                    if keyframe_id in self.keyframe_id_to_timestamp:
                        timestamp = self.keyframe_id_to_timestamp[keyframe_id]
                        image_name = timestamp.replace(".", "").strip()
                        print(f"WE MUST RETRIEVE KEYFRAME {keyframe_id} => {timestamp} for point {idx} at {self.points[idx]}")
                        try:
                            copy_img(f"{img_input_dir}/{image_name}.png", f"{output_dir}/{bin_key}/Images/{image_name}.png")
                        except FileNotFoundError:
                            pass
                            #print("There is no keyframe ", {image_name})
                    else:
                        #print(f"We are missing a mapping for keyframe id ", keyframe_id)
                        pass

            write_point_cloud(pcd, f"{output_dir}/{bin_key}/svin_{bin_key}.ply")

def main():
    root_path = "/home/luke/Documents/peace2/peace"
    splitter = PCSplitter(f"{root_path}/LeftonRigLeft/pointcloud_2025-11-08_20-56-01.ply", f"{root_path}/LeftonRigLeft/keyframe_observations_2025_11_08_20_55_44.txt")
    splitter.id_points()
    splitter.build_timestamp_database(f"{root_path}/LeftonRigLeft/keyframes_2025_11_08_20_55_45.txt")
    print(len(splitter.keyframes_by_point_id))

    #splitter.get_keyframes_by_point(-9.83456, 2.81985, -5.03363)

    # A couple (as in literally two) of the points are missing for some reason
    # Ask Chinmay, probably a bug.
    for idx in range(len(splitter.points)):
        if idx not in splitter.keyframes_by_point_id:
            print(f"{idx} is mysteriously missing")
            splitter.keyframes_by_point_id[idx] = set()

    splitter.bin_points(50, overlap_thresh=0.2)
    splitter.write_bins(f"{root_path}/LeftonRigLeft/keyframes", f"{root_path}/coob5")

    #splitter.get_keyframes_by_point(-9.83456, 2.81985, -5.03363)

if __name__ == "__main__":
    main()