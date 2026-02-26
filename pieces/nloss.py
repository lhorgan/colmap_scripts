import os
import numpy as np
from sweep import write_point_cloud, read_point_cloud
import open3d as o3d

def main():
    root_path = "/home/luke/Documents/nloss"
    plys_path = f"{root_path}/aligned_spheres"

    ply_names = os.listdir(plys_path)
    
    all_points = np.zeros((0, 3))
    point_idx_to_submap_idx = np.zeros(0)

    print("Making sublists")
    for (i, ply_name) in enumerate(ply_names):
        pcd = read_point_cloud(f"{plys_path}/{ply_name}")
        
        points = np.array(pcd.points)
        sample_count = max(min(100, len(points)), int(0.01*len(points)))
        indices = np.random.choice(len(points), size=sample_count, replace=False)
        
        sublist = points[indices]
        indices_for_sublist = np.ones(len(sublist)) * i

        all_points = np.concat((all_points, sublist))
        point_idx_to_submap_idx = np.concat((point_idx_to_submap_idx, indices_for_sublist))
    
    print("Making the KD tree")
    pcd = o3d.geometry.PointCloud()
    pcd.points = o3d.utility.Vector3dVector(all_points)
    pcd_tree = o3d.geometry.KDTreeFlann(pcd)
    print("KD tree complete")

    print("Getting nearest neighbors")
    k = 100  # number of nearest neighbors (includes the point itself)

    total_dist = 0
    num_points = 0

    for i, point in enumerate(all_points):
        my_submap_idx = point_idx_to_submap_idx[i]
        count, indices, distances = pcd_tree.search_knn_vector_3d(point, k)
        for (j, idx) in enumerate(indices):
            neighbor_submap_idx = point_idx_to_submap_idx[idx]
            if neighbor_submap_idx != my_submap_idx:
                dist = distances[j]
                if dist < 0.25: # sqrt(dist) < 0.5 is what we really want
                    total_dist += dist
                    num_points += 1
                    print(f"Found a neighbor for {my_submap_idx} in {neighbor_submap_idx} at distance {np.sqrt(distances[j])}")
                    break

    
    n_loss = total_dist / num_points
    return n_loss

if __name__ == "__main__":
    main()