import numpy as np
import os
from pathlib import Path
import shutil

def filter_svin(input_path, output_path, images_path):
    images_set = set()
    svin_set = set()

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
            svin_set.add(img_name)
            if img_name in images_set:
                #print(img_name, "is in the set")
                count += 1
                f.write(line)
            else:
                print(f"Did not find {img_name} in the directory. Removing it from SVIN file.")
    
    print("Added", count)

def copy_image(input_path, output_path):
    source = Path(input_path)
    destination = Path(output_path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    new_path = shutil.copy2(source, destination)
    return Path(new_path)

class Pipeline:
    def __init__(self, svin_path):
        self.svin_path = svin_path
        self.poses = {}

    def read_svin_file(self):
        with open(self.svin_path) as f:
            for line in f:
                if line.startswith("#"):
                    continue

                timestamp = line.split(" ")[0]
                image_name = f"{timestamp.replace('.', '')}.png"
                pose = [float(x) for x in (line.split(" ")[1:])]
                self.poses[image_name] = pose
    
    def get_cam_centers(self):
        cam_centers = np.zeros((len(self.poses), 3))
        i = 0
        for image_name in self.poses:
            pose = self.poses[image_name]
            cam_centers[i] = np.array(pose[:3])
            i += 1
        return cam_centers

    def get_bounds(self, points):
        min_x = np.min(points[:,0])
        max_x = np.max(points[:,0])

        min_y = np.min(points[:,1])
        max_y = np.max(points[:,1])

        min_z = np.min(points[:,2])
        max_z = np.max(points[:,2])

        return [min_x, max_x, min_y, max_y, min_z, max_z]

    def bin_points(self, bin_count, points):
        n = bin_count
        min_x, max_x, min_y, max_y, min_z, max_z = self.get_bounds(points)
        lx = max_x - min_x
        ly = max_y - min_y
        lz = max_z - min_z

        nx = ((n * lx**2) / (ly * lz))**(1/3)
        ny = ((n * ly**2) / (lx * lz))**(1/3)
        nz = ((n * lz**2) / (lx * ly))**(1/3)

        lb = lx / nx

        #print(nx, ny, nz)

        bins = {}
        for image_name in self.poses:
            pose = self.poses[image_name]
            x, y, z = np.array(pose[:3])

            bin_x = int((x - min_x) // lb)
            bin_y = int((y - min_y) // lb)
            bin_z = int((z - min_z) // lb)
            
            bin_key = self.inds_to_key(bin_x, bin_y, bin_z)
            if bin_key not in bins:
                bins[bin_key] = []
            bins[bin_key].append(image_name)
        
        total_len = 0
        for key in bins:
            #print(key, len(bins[key]))
            total_len += len(bins[key])
        #print("TOTAL LEN", total_len)

        return bins
    
    def merge_bins(self, bins, target_size):
        used_bins = set()
        super_bins = []

        #for bin_key in ["bin_72_4_18"]:
        for bin_key in bins:
            if bin_key in used_bins:
                continue

            super_bin = set()
            super_bin_img_count = 0

            bin_queue = [bin_key]

            while len(bin_queue) > 0:
                curr_bin_key = bin_queue.pop(0)

                #print("Examining bin ", curr_bin_key)

                curr_imgs = bins[curr_bin_key]
                
                if super_bin_img_count + len(curr_imgs) > target_size:
                    break
                
                super_bin.add(curr_bin_key)
                used_bins.add(curr_bin_key)
                super_bin_img_count += len(curr_imgs)

                x, y, z = self.key_to_inds(curr_bin_key)
                
                # n is for neighbors
                neighbors = [(x-1, y, z),
                             (x+1, y, z),
                             (x, y-1, z),
                             (x, y+1, z),
                             (x, y, z-1),
                             (x, y, z+1)]
                for nx, ny, nz in neighbors:
                    n_key = self.inds_to_key(nx, ny, nz)
                    if n_key in bins and not n_key in used_bins:
                        bin_queue.append(n_key)

            super_bins.append(super_bin)
            #print(super_bin)
            #print("total images in bin", super_bin_img_count)
        
        return super_bins
    
    def merge_from_super_bins(self, super_bins, bins):
        print("super bins", len(super_bins))
        merged_bins = {}
        bin_ind = 0
        for super_bin in super_bins:
            merged_bin_key = f"bin_{bin_ind}"
            merged_bins[merged_bin_key] = []
            for bin_key in super_bin:
                imgs = bins[bin_key]
                merged_bins[merged_bin_key] += imgs
            bin_ind += 1
        
        return merged_bins

    def key_to_inds(self, key):
        return [int(x) for x in key.split("_")[1:]]

    def inds_to_key(self, x, y, z):
        return f"bin_{x}_{y}_{z}"

    def make_directories(self, input_path, copy_path, binned_imgs):
        total_imgs_copied = set()
        for bin_key in binned_imgs:
            imgs = binned_imgs[bin_key]
            for img in imgs:
                src_path = os.path.join(input_path, img)
                dst_path = os.path.join(copy_path, bin_key, "Images", img)
                total_imgs_copied.add(dst_path)
                copy_image(src_path, dst_path)

#pipeline = Pipeline("/home/luke/Documents/datasets/Left/svin_LeftOnRig_Depth_introduced.txt")
pipeline = Pipeline("/home/luke/Documents/datasets/Combined/svin_orig.txt")
pipeline.read_svin_file()
points = pipeline.get_cam_centers()
binned_imgs = pipeline.bin_points(50000, points)
pipeline.make_directories(input_path="/home/luke/Documents/datasets/Combined/Images/", copy_path="/home/luke/Documents/datasets/Cubes", binned_imgs=binned_imgs)
super_bins = pipeline.merge_bins(binned_imgs, 200)
merged_bins = pipeline.merge_from_super_bins(super_bins, binned_imgs)
pipeline.make_directories(input_path="/home/luke/Documents/datasets/Combined/Images/", copy_path="/home/luke/Documents/datasets/MergedCubes", binned_imgs=merged_bins)

#print(points)

# bounds = pipeline.get_bounds(points)
# print(bounds)