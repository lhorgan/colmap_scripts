import pickle
import os

def go():
    base_path = "/mnt/disk_1_ssd/luke/blub"
    unexpanded_clusters_path = f"{base_path}/unexpanded_clusters.pkl"
    spheres_path = f"{base_path}/spheres"

    with open(unexpanded_clusters_path, "rb") as f:
        clusters = pickle.load(f)
    
    for i in range(len(clusters)):
        cluster_name = f"cluster_{i}"
        sparse_path = f"{spheres_path}/{cluster_name}/sparse"
        for model_name in sparse_path: # 0, 1, etc
            svin_from_colmap_path = f"{sparse_path}/{model_name}/svin_from_colmap_inv.txt"
            
        
go()