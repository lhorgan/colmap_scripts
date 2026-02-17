# https://gemini.google.com/app/b39829f92f89df2f

import torch
import math
import numpy as np
import os
import pickle
import open3d as o3d

from sweep import write_point_cloud, read_point_cloud
from make_overlap_graph import FancyList

np.set_printoptions(precision=3, suppress=True)

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
        optimizer, mode='min', factor=0.5, patience=50, verbose=True
    )

    for step in range(2000):
        transforms = params_to_transforms(params_by_key)
        loss = compute_loss(points3D_by_model, overlaps, transforms)
        #print("DAS LOSS: ", loss)
        
        scheduler.step(loss)

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
        
        if step % 50 == 0:
            print(f"Step {step}: Loss = {loss.item():.6f}")
    
    for key in points3D_by_model:
        panel = points3D_by_model[key]
        T = transforms[key]
        #print(T)
        panel_transformed = (T @ panel.T).T
        pcd = homogeneous_to_pointcloud(panel_transformed)
        write_point_cloud(pcd, f"/home/luke/Documents/titanic/refined_spheres_2/{key}.ply")

# https://claude.ai/chat/08c4db9b-3f94-4759-a39f-027038330fb9
# This one function is by Claude
def homogeneous_to_pointcloud(vectors):
    pcd = o3d.geometry.PointCloud()
    
    # Divide by last column (w coordinate)
    points_3d = vectors[:, :3] / vectors[:, 3:4]
    
    pcd.points = o3d.utility.Vector3dVector(points_3d.detach().numpy())
    return pcd

def compute_loss(points_by_model, overlaps, transforms):
    loss = 0

    transformed_points = {}
    for model_key in points_by_model:
        #theta, rho = parse_key(key)
        points = points_by_model[model_key]
        M = transforms[model_key]
        points_transformed = (M @ points.T).T
        transformed_points[model_key] = points_transformed
    
    for overlap_key in overlaps:
        model_key0, model_key1 = overlap_key.split(":")

        if model_key0 in transformed_points and model_key1 in transformed_points:
            #print(f"WALP: {model_key0}, {model_key1}")
            overlap_inds0 = overlaps[overlap_key][0].as_list()
            overlap_inds1 = overlaps[overlap_key][1].as_list()

            points0 = transformed_points[model_key0][overlap_inds0]
            points1 = transformed_points[model_key1][overlap_inds1]

            curr_loss = torch.sqrt(torch.sum(torch.square(points0 - points1)))
            #curr_loss = torch.mean(torch.sum(torch.square(points0 - points1), dim=1)) # Claude tip
            
            #print(f"CURR LOSS {model_key0}, {model_key1}", curr_loss)
            loss += curr_loss
    
    return loss

def main():
    root_path = "/home/luke/Documents/titanic"
    plys_path = f"{root_path}/aligned_spheres"
    overlaps_path = f"{root_path}/pickle/overlaps.pkl"

    ply_names = os.listdir(plys_path)
    points_by_model = {}
    for ply_name in ply_names:
        print(ply_name)
        model_key = ply_name.split(".")[0]
        pcd = read_point_cloud(f"{plys_path}/{ply_name}")

        points = np.array(pcd.points)
        homog_points = np.column_stack([points, np.ones(points.shape[0])])
        points_by_model[model_key] = torch.tensor(homog_points, dtype=torch.float32)

    with open(overlaps_path, "rb") as f:
        point3Ds_by_model, overlaps_graph = pickle.load(f)

    print("\n\n")

    # print("OVERLAPS GRAPH HAS THE FOLLOWING KEYS")
    # for model_key in overlaps_graph:
    #     print(model_key)
    
    go(points_by_model, overlaps_graph)

if __name__ == "__main__":
    main()
