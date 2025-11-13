import torch
import math
import numpy as np
import os
import pickle
import open3d as o3d

from refine import read_point_cloud, write_point_cloud
from sweep import make_key, parse_key, get_bottom_neighbor, get_left_neighbor, get_right_neighbor, get_top_neighbor

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

def go2(panels, overlaps):
    params = []
    params_by_key = {}
    for key in panels:
        t = (torch.rand(3) * 0.5 - 0.25).requires_grad_()
        #t = torch.tensor([0, 0, 0], requires_grad=True, dtype=torch.float32)
        q = torch.tensor([1.0, 0.0, 0.0, 0.0], requires_grad=True)

        params.append(t)
        params.append(q)

        params_by_key[key] = (t, q)
        
    optimizer = torch.optim.Adam(params, lr=0.01)
    for step in range(10000):
        transforms = params_to_transforms(params_by_key)
        loss = compute_loss(panels, overlaps, transforms)
        
        loss.backward()

        # for key in params_by_key:
        #     t_static, q_static = params_by_key[key]
        #     print(f"{key}, Gradient for t_static: {t_static.grad}")
        #     print(f"{key}, Gradient for q_static: {q_static.grad}")
        #     print("\n")

        optimizer.step()
        optimizer.zero_grad()
        
        if step % 50 == 0:
            print(f"Step {step}: Loss = {loss.item():.6f}")
    
    for key in panels:
        panel = panels[key]
        T = transforms[key]
        #print(T)
        panel_transformed = (T @ panel.T).T
        pcd = homogeneous_to_pointcloud(panel_transformed)
        write_point_cloud(pcd, f"/home/luke/Documents/xmas2/fixed/{key}.ply")

# https://claude.ai/chat/08c4db9b-3f94-4759-a39f-027038330fb9
# This one function is by Claude
def homogeneous_to_pointcloud(vectors):
    pcd = o3d.geometry.PointCloud()
    
    # Divide by last column (w coordinate)
    points_3d = vectors[:, :3] / vectors[:, 3:4]
    
    pcd.points = o3d.utility.Vector3dVector(points_3d.detach().numpy())
    return pcd

def compute_loss(panels, overlaps, transforms):
    loss = 0

    transformed_panels = {}
    for key in panels:
        #theta, rho = parse_key(key)
        panel = panels[key]
        M = transforms[key]
        panel_transformed = (M @ panel.T).T
        transformed_panels[key] = panel_transformed
    
    for key in transformed_panels:
        for direction in ["right", "top"]:
            overlap = get_overlapping_points(key, transformed_panels, overlaps, direction)
            if overlap is None:
                continue
            my_overlap_with_you, your_overlap_with_me = overlap
            curr_loss = torch.sqrt(torch.sum(torch.square(my_overlap_with_you - your_overlap_with_me)))
            # if curr_loss > 1:
            #     pcd1 = homogeneous_to_pointcloud(my_overlap_with_you)
            #     pcd2 = homogeneous_to_pointcloud(your_overlap_with_me)
            #     write_point_cloud(pcd1, f"/home/luke/Documents/xmas2/overlapcheck/{key}_my_with_you.ply")
            #     write_point_cloud(pcd2, f"/home/luke/Documents/xmas2/overlapcheck/{key}_yours_with_me.ply")
            #     print(f"Loss for panel {key}, {direction} is ", curr_loss)
            loss += curr_loss
    
    return loss

def get_neighbor(key, panels, direction):
    funcs = {"top": get_top_neighbor, "left": get_left_neighbor, "right": get_right_neighbor, "bottom": get_bottom_neighbor}
    return funcs[direction](key, panels)

def get_overlapping_points(key, panels, overlaps, direction):
    correspondences = {"top": "bottom", "right": "left"}

    panel = panels[key]
    start_ind, end_ind = overlaps[key][direction]
    my_overlap_with_you = panel[start_ind:end_ind]

    neighbor_key, neighbor = get_neighbor(key, panels, direction)
    if neighbor_key is None:
        return None

    start_ind, end_ind = overlaps[neighbor_key][correspondences[direction]]
    your_overlap_with_me = neighbor[start_ind:end_ind]

    if len(my_overlap_with_you) != len(your_overlap_with_me):
        print("overlap mismatch")
        return None # This should never actually happen

    return my_overlap_with_you, your_overlap_with_me

def main():
    root = "/home/luke/Documents/xmas2"
    panel_filenames = os.listdir(f"{root}/cracked")

    panels = {}
    for fname in panel_filenames:
        pcd = read_point_cloud(f"{root}/cracked/{fname}")
        theta, rho = [int(angle) for angle in fname[:-4].split("_")[1:]]
        key = make_key(theta, rho)
        points = np.array(pcd.points)
        homog_points = np.column_stack([points, np.ones(points.shape[0])])
        panels[key] = torch.tensor(homog_points, dtype=torch.float32)
    
    with open(f"{root}/cracked_overlaps.pkl", "rb") as f:
        overlaps = pickle.load(f)

    #print(overlaps)
    go2(panels, overlaps)

if __name__ == "__main__":
    main()
