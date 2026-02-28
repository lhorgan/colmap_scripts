# https://gemini.google.com/app/b39829f92f89df2f

import torch
import numpy as np
import os
import pickle
import open3d as o3d

from util import write_point_cloud, read_point_cloud
from make_overlap_graph import FancyList

np.set_printoptions(precision=3, suppress=True)

def make_overlap_key(my_model_key, other_model_key):
    ordered_model_keys = sorted([my_model_key, other_model_key])
    overlap_key = ":".join(ordered_model_keys)
    return overlap_key

def quat_to_matrix(q):
    q = q / (torch.norm(q) + 1e-8) 
    
    w, x, y, z = q[0], q[1], q[2], q[3]
    
    R = torch.zeros((3, 3))
    R[0, 0] = 1 - 2*y*y - 2*z*z
    R[0, 1] = 2*x*y - 2*w*z
    R[0, 2] = 2*x*z + 2*w*y
    
    R[1, 0] = 2*x*y + 2*w*z
    R[1, 1] = 1 - 2*x*x - 2*z*z
    R[1, 2] = 2*y*z - 2*w*x
    
    R[2, 0] = 2*x*z - 2*w*y
    R[2, 1] = 2*y*z + 2*w*x
    R[2, 2] = 1 - 2*x*x - 2*y*y
    return R

def params_to_transforms(params_by_key):
    transforms = {}
    for key in params_by_key:
        t, q = params_by_key[key]

        R = quat_to_matrix(q)

        T = torch.eye(4)
        T[0:3, 0:3] = R
        T[0:3, 3] = t

        transforms[key] = T
    
    return transforms

def go(points3D_by_model, overlaps):
    params = []
    params_by_key = {}
    for model_key in points3D_by_model:
        #t = (torch.rand(3) * 0.5 - 0.25).requires_grad_()
        t = torch.tensor([0, 0, 0], requires_grad=True, dtype=torch.float32)
        q = torch.tensor([1.0, 0.0, 0.0, 0.0], requires_grad=True)

        params.append(t)
        params.append(q)

        params_by_key[model_key] = (t, q)
        
    optimizer = torch.optim.Adam(params, lr=0.01)
    
    # Claude tip
    scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(
        optimizer, mode='min', factor=0.5, patience=50
    )

    for step in range(20):
        transforms = params_to_transforms(params_by_key)
        transformed_points = get_transformed_points(points3D_by_model, transforms)
        nn_overlaps = build_kd_tree(points3D_by_model)

        loss1 = compute_overlap_loss(overlaps, transformed_points)
        loss2 = compute_overlap_loss(nn_overlaps, transformed_points)
        print("LOSS 2: ", loss2)

        loss = loss1 + 0.3 * loss2
        #print("DAS LOSS: ", loss)
        
        scheduler.step(loss.detach()) # detach prevents a warning

        loss.backward()

        # for key in params_by_key:
        #     t_static, q_static = params_by_key[key]
        #     print(f"{key}, Gradient for t_static: {t_static.grad}")
        #     print(f"{key}, Gradient for q_static: {q_static.grad}")
        #     print("\n")

        optimizer.step()
        optimizer.zero_grad()

        # Re-normalize quaternions, Claude tip
        with torch.no_grad():
            for key in params_by_key:
                t, q = params_by_key[key]
                q.data = q.data / torch.norm(q.data)
        
        if step % 1 == 0:
            print(f"Step {step}: Loss = {loss.item():.6f}")
    
    for key in points3D_by_model:
        panel = points3D_by_model[key]
        T = transforms[key]
        #print(T)
        panel_transformed = (T @ panel.T).T
        pcd = homogeneous_to_pointcloud(panel_transformed)
        write_point_cloud(pcd, f"/home/luke/Documents/caaves/refined_spheres_bw/{key}.ply")

def add_to_overlap_graph(my_model_key, my_index, other_model_key, other_index, overlap_graph):
    indexes = {}
    indexes[my_model_key] = my_index
    indexes[other_model_key] = other_index

    ordered_model_keys = sorted([my_model_key, other_model_key])
    overlap_key = ":".join(ordered_model_keys)
    model_key_0, model_key_1 = ordered_model_keys

    if overlap_key not in overlap_graph:
        overlap_graph[overlap_key] = (FancyList(), FancyList())
    
    index0 = indexes[model_key_0]
    index1 = indexes[model_key_1]

    if not overlap_graph[overlap_key][0].contains(index0) and not overlap_graph[overlap_key][1].contains(index1):
        overlap_graph[overlap_key][0].add(index0)
        overlap_graph[overlap_key][1].add(index1)

# https://claude.ai/chat/08c4db9b-3f94-4759-a39f-027038330fb9
# This one function is by Claude
def homogeneous_to_pointcloud(vectors):
    pcd = o3d.geometry.PointCloud()
    
    # Divide by last column (w coordinate)
    points_3d = vectors[:, :3] / vectors[:, 3:4]
    
    pcd.points = o3d.utility.Vector3dVector(points_3d.detach().numpy())
    return pcd

def get_transformed_points(points_by_model, transforms):
    transformed_points = {}
    for model_key in points_by_model:
        #theta, rho = parse_key(key)
        points = points_by_model[model_key]
        M = transforms[model_key]
        points_transformed = (M @ points.T).T[:,:3] # drop the homogeneous coordiante, which is 1, does not actually matter
        #print(points_transformed)
        transformed_points[model_key] = points_transformed

    return transformed_points

def build_kd_tree(points_by_model):
    #print("building a kd tree")
    points_list = []
    pcd = o3d.geometry.PointCloud()

    all_points = np.zeros((0, 3))
    point_idx_to_submap_idx = np.zeros(0).astype(np.uint32)
    global_idx_to_local_idx = np.zeros(0).astype(np.uint32)

    chosen_indices_by_model = {}
    i_to_model = {}

    for (i, model) in enumerate(points_by_model):
        points = points_by_model[model].detach().cpu().numpy()[:, :3] # Drop the homogeneous coordinate
        sample_count = max(min(100, len(points)), int(0.01*len(points)))
        indices = np.random.choice(len(points), size=sample_count, replace=False)
        i_to_model[i] = model

        sublist = points[indices]
        indices_for_sublist = np.ones(len(sublist)) * i

        all_points = np.concat((all_points, sublist))
        point_idx_to_submap_idx = np.concat((point_idx_to_submap_idx, indices_for_sublist))
        global_idx_to_local_idx = np.concat((global_idx_to_local_idx, indices))

    #print("Making the KD tree")
    pcd = o3d.geometry.PointCloud()
    pcd.points = o3d.utility.Vector3dVector(all_points)
    pcd_tree = o3d.geometry.KDTreeFlann(pcd)
    #print("KD tree complete")

    #print("Getting nearest neighbors")
    k = 100  # number of nearest neighbors (includes the point itself)

    total_dist = 0
    num_points = 0

    overlap_graph = {}

    for i, point in enumerate(all_points):
        my_submap_idx = point_idx_to_submap_idx[i]
        
        my_model = i_to_model[my_submap_idx]
        my_submap_local_idx = global_idx_to_local_idx[i]

        count, indices, distances = pcd_tree.search_knn_vector_3d(point, k)
        for (j, idx) in enumerate(indices):
            neighbor_submap_idx = point_idx_to_submap_idx[idx]
            if neighbor_submap_idx != my_submap_idx:
                dist = distances[j]
                if dist < 0.25: # sqrt(dist) < 0.5 is what we really want
                    #print(total_dist)
                    neighbor_model = i_to_model[neighbor_submap_idx]
                    neighbor_submap_local_idx = global_idx_to_local_idx[idx]

                    #print("NEIGHBOR SUBMAP INDEX IS", neighbor_submap_idx)
                    
                    add_to_overlap_graph(my_model, my_submap_local_idx, neighbor_model, neighbor_submap_local_idx, overlap_graph)
                    my_point = points_by_model[my_model][my_submap_local_idx]
                    their_point = points_by_model[neighbor_model][neighbor_submap_local_idx]
                    le_dist = torch.sqrt(torch.sum((my_point - their_point) ** 2))
                    #print(f"Adding to overlap graph an overlap between {my_submap_local_idx} in {my_model} and {neighbor_submap_local_idx} in {neighbor_model}, which has distance {le_dist}, vs {np.sqrt(dist)}.")

                    total_dist += dist
                    num_points += 1
                    #print(f"Found a neighbor for {my_submap_idx} in {neighbor_submap_idx} at distance {(distances[j])}")
                    break
    
    # overlaps = overlap_graph
    # for overlap_key in overlap_graph:
    #     model_key0, model_key1 = overlap_key.split(":")
    #     overlap_inds0 = overlaps[overlap_key][0].as_list()
    #     overlap_inds1 = overlaps[overlap_key][1].as_list()
    #     points0 = points_by_model[model_key0][overlap_inds0]
    #     points1 = points_by_model[model_key1][overlap_inds1]

    #     print("wtah ", torch.mean(torch.sum(torch.square(points0 - points1), dim=1)))

    #     print(points0[0])
    #     print(points1[0])
    #     print("\n")

    n_loss = total_dist / num_points
    #print("n_loss is ", n_loss)
    #print(n_loss)
    return overlap_graph

def compute_overlap_loss(overlaps, transformed_points):
    loss = 0

    for overlap_key in overlaps:
        model_key0, model_key1 = overlap_key.split(":")

        if model_key0 in transformed_points and model_key1 in transformed_points:
            #print(f"WALP: {model_key0}, {model_key1}")
            overlap_inds0 = overlaps[overlap_key][0].as_list()
            overlap_inds1 = overlaps[overlap_key][1].as_list()
            
            #sample_count = max(min(100, len(overlap_inds0)), int(0.1*len(overlap_inds0)))
            #indices = np.random.choice(len(overlap_inds0), size=sample_count, replace=False)
            #overlap_inds0 = np.array(overlap_inds0)[indices].tolist()
            #overlap_inds1 = np.array(overlap_inds1)[indices].tolist()

            #print(len(overlap_inds0), len(overlap_inds1))

            #print(type(overlap_inds0))
            #print(type(overlap_inds0_rand))

            #print(len(overlap_inds0))
            #print(len(overlap_inds0_rand))
            #print("\n\n")

            points0 = transformed_points[model_key0][overlap_inds0]
            points1 = transformed_points[model_key1][overlap_inds1]

            #curr_loss = torch.sqrt(torch.sum(torch.square(points0 - points1)))
            curr_loss = torch.mean(torch.sum(torch.square(points0 - points1), dim=1)) # Claude tip
            
            #print(f"CURR LOSS {model_key0}, {model_key1}", curr_loss)
            loss += curr_loss
    
    #nloss = build_kd_tree(transformed_points)
    #print(nloss)
    #print(f"nloss is ", nloss)

    return loss

def main():
    root_path = "/mnt/disk_1_ssd/luke/blub"
    plys_path = f"{root_path}/aligned_spheres"
    overlaps_path = f"{root_path}/pickle/overlaps.pkl"

    ply_names = os.listdir(plys_path)
    points_by_model = {}
    for ply_name in ply_names:
        #print(ply_name)
        model_key = ply_name.split(".")[0]
        pcd = read_point_cloud(f"{plys_path}/{ply_name}")

        points = np.array(pcd.points)
        homog_points = np.column_stack([points, np.ones(points.shape[0])])
        points_by_model[model_key] = torch.tensor(homog_points, dtype=torch.float32)

    with open(overlaps_path, "rb") as f:
        point3Ds_by_model, overlaps_graph = pickle.load(f)

    #print("\n\n")

    # print("OVERLAPS GRAPH HAS THE FOLLOWING KEYS")
    # for model_key in overlaps_graph:
    #     print(model_key)
    
    go(points_by_model, overlaps_graph)

if __name__ == "__main__":
    main()
