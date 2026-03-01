import pickle
import os
from rotate_svin_traj import *
from plot_cams import *

def filter_svin(input_path, output_path, cluster_set):
    svin_set = set()

    with open(input_path) as f:
        lines = f.readlines()
    
    count = 0
    with open(output_path, "w+") as f:
        comment = lines[0]
        f.write(comment)

        for line in lines[1:]:
            timestamp = f'{(line.split(" ")[0]).replace(".", "")}'
            svin_set.add(timestamp)
            if timestamp in cluster_set:
                #print(img_name, "is in the set")
                count += 1
                f.write(line)
            else:
                #print(f"Did not find {img_name} in the directory. Removing it from SVIN file.")
                pass
    
    print("Added", count)

def merge_svins(input_dir, output_path):
    files = [os.path.join(input_dir, f) for f in os.listdir(input_dir)]
    
    comment = None
    body_lines = []

    for filepath in files:
        with open(filepath, 'r') as f:
            for line in f:
                line = line.rstrip('\n')
                if line.startswith('#'):
                    if comment is None:
                        comment = line
                elif line.strip():  # skip blank lines
                    body_lines.append(line)

    with open(output_path, 'w') as out:
        if comment:
            out.write(comment + '\n')
        for line in body_lines:
            out.write(line + '\n')

def go(base_path, output_dir_name, torch_transforms_path):
    base_path = "/mnt/disk_1_ssd/luke/blub"
    
    unexpanded_clusters_path = f"{base_path}/unexpanded_clusters.pkl"
    torch_transforms_path = torch_transforms_path#f"{base_path}/torch_transforms.pkl"

    #spheres_path = f"{base_path}/spheres"
    aligned_poses_path = f"{base_path}/{output_dir_name}/aligned_poses"
    aligned_poses_disjoint_path = f"{base_path}/{output_dir_name}/aligned_poses_disjoint"
    refined_poses_path = f"{base_path}/{output_dir_name}/refined_poses"
    refined_poses_plys_path = f"{base_path}/{output_dir_name}/refined_poses_plys"

    with open(unexpanded_clusters_path, "rb") as f:
        clusters = pickle.load(f)

    with open(torch_transforms_path, "rb") as f:
        torch_transforms = pickle.load(f)
    
    transforms = {}
    for model_key in torch_transforms:
        transforms[model_key] = torch_transforms[model_key].detach().cpu().numpy()
        #print(transforms[model_key])

    cluster_sets = []
    for i in range(len(clusters)):
        cluster_sets.append(set(clusters[i]))
    
    for fname in os.listdir(aligned_poses_path):
        model_key = fname.split(".")[0]
        cluster_info = model_key.split("_")[1]
        cluster = int(cluster_info.split("-")[0])
        model = int(cluster_info.split("-")[0])
        filter_svin(input_path=f"{aligned_poses_path}/{fname}", output_path=f"{aligned_poses_disjoint_path}/{fname}", cluster_set=cluster_sets[cluster])
        M = transforms[model_key]
        rotate_svin_traj(input_path=f"{aligned_poses_disjoint_path}/{fname}", output_path=f"{refined_poses_path}/{fname}", M=M)
        plot_cameras(f"{refined_poses_path}/{fname}", 0.00008, f"{refined_poses_plys_path}/{fname.split('.')[0]}.ply")    

    merge_svins(input_dir=aligned_poses_path, output_path=f"{base_path}/{output_dir_name}/aligned_poses_merged.txt")
    merge_svins(input_dir=refined_poses_path, output_path=f"{base_path}/{output_dir_name}/refined_poses_merged.txt")        
        
if __name__ == "__main__":
    go(base_path="/mnt/disk_1_ssd/luke/blub", output_dir_name="traj_dual_loss", torch_transforms_path="/mnt/disk_1_ssd/luke/blub/torch_transforms.pkl")
    go(base_path="/mnt/disk_1_ssd/luke/blub", output_dir_name="traj_smpl_loss", torch_transforms_path="/mnt/disk_1_ssd/luke/blub/torch_transforms_test.pkl")