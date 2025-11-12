import random
import math
import open3d as o3d
import numpy as np
import pickle

from refine import read_point_cloud, write_point_cloud

def sind(deg):
    return math.sin(deg * math.pi / 180)

def cosd(deg):
    return math.cos(deg * math.pi / 180)

def sweep(r1, r2, theta1, theta2, rho1, rho2, point_count=1000):
    point_cloud = o3d.geometry.PointCloud()
    points = np.zeros((point_count, 3))

    for i in range(point_count):
        r = random.uniform(r1, r2)
        theta = random.uniform(theta1, theta2)
        rho = random.uniform(rho1, rho2)

        x1 = r * cosd(theta)
        z = r * sind(theta)
        
        x = x1 * cosd(rho)
        y = x1 * sind(rho)

        # Add this point (x, y, z) to the point cloud
        points[i] = [x, y, z]
    
    point_cloud.points = o3d.utility.Vector3dVector(points)
    return point_cloud

def parse_key(key):
    theta, rho = [int(angle) for angle in key.split("_")]
    return theta, rho

def make_key(theta, rho):
    return f"{theta}_{rho}"

def get_top_neighbor(key, panels):
    theta, rho = parse_key(key)
    if theta == 30:
        return None, [o3d.geometry.PointCloud() for _ in range(5)]
    neighbor_key = make_key(theta + 30, rho)
    return neighbor_key, panels[neighbor_key]

def get_bottom_neighbor(key, panels):
    theta, rho = parse_key(key)
    if theta == -60:
        return None, [o3d.geometry.PointCloud() for _ in range(5)]
    neighbor_key = make_key(theta - 30, rho)
    return neighbor_key, panels[neighbor_key]

def get_left_neighbor(key, panels):
    theta, rho = parse_key(key)
    neighbor_key = make_key(theta, (rho - 30) % 360)
    return neighbor_key, panels[neighbor_key]
    
def get_right_neighbor(key, panels):
    theta, rho = parse_key(key)
    neighbor_key = make_key(theta, (rho + 30) % 360)
    return neighbor_key, panels[neighbor_key]

def main():
    folder = "/home/luke/Documents/xmas2/cracked"

    panels = {}

    for theta in range(-60, 60, 30):
        for rho in range(0, 360, 30):
            bottom = sweep(10, 10.1, theta, theta + 1, rho, rho + 30, 200)

            left = sweep(10, 10.1, theta + 1, theta + 29, rho, rho + 1, 200)
            center = sweep(10, 10.1, theta + 1, theta + 29, rho + 1, rho + 29, 5000)
            right = sweep(10, 10.1, theta + 1, theta + 29, rho + 29, rho + 30, 200)

            top = sweep(10, 10.1, theta + 29, theta + 30, rho, rho + 30, 200)

            #write_point_cloud(center, f"{folder}/slice_{theta}_{rho}_center.ply", color=[0, 0, 1])

            panels[f"{theta}_{rho}"] =  [top, left, center, right, bottom]
    
    overlaps = {}
    clouds = {}

    for key in panels:
        theta, rho = [int(angle) for angle in key.split("_")]

        top, left, center, right, bottom = panels[key]
        
        _, n_left = get_left_neighbor(key, panels)
        _, n_right = get_right_neighbor(key, panels)
        _, n_top = get_top_neighbor(key, panels)
        _, n_bottom = get_bottom_neighbor(key, panels)

        #gah = "/home/luke/Documents/xmas2/gah"
        # write_point_cloud(center, f"{gah}/center.ply")
        # write_point_cloud(n_left[2], f"{gah}/left.ply")
        # write_point_cloud(n_right[2], f"{gah}/right.ply")
        # write_point_cloud(n_top[2], f"{gah}/top.ply")
        # write_point_cloud(n_bottom[2], f"{gah}/bottom.ply")
        # # write_point_cloud(top, f"{gah}/top.ply")
        # # write_point_cloud(left, f"{gah}/left.ply")
        # # write_point_cloud(center, f"{gah}/center.ply")
        # # write_point_cloud(right, f"{gah}/right.ply")
        # # write_point_cloud(bottom, f"{gah}/bottom.ply")
        # break

        left_frame = n_left[3] # Right of the left
        right_frame = n_right[1] # Left of the right
        top_frame = n_top[4] # Bottom of the top
        bottom_frame = n_bottom[0] # Top of the bottom

        full_panel = top + top_frame + \
                     left + left_frame + \
                     right_frame + right + \
                     bottom_frame + bottom + \
                     center


        # write_point_cloud(center, f"{gah}/center.ply")
        # write_point_cloud(left_frame, f"{gah}/left.ply")
        # write_point_cloud(right_frame, f"{gah}/right.ply")
        # write_point_cloud(top_frame, f"{gah}/top.ply")
        # write_point_cloud(bottom_frame, f"{gah}/bottom.ply")

        top_start =  0
        left_start = top_start + len(top.points) + len(top_frame.points)
        right_start = left_start + len(left.points) + len(left_frame.points)
        bottom_start = right_start + len(right_frame.points) + len(right.points)
        
        overlaps[make_key(theta, rho)] = {
            "top": (top_start, top_start            + len(top.points)       + len(top_frame.points)),
            "left": (left_start, left_start         + len(left.points)      + len(left_frame.points)),
            "right":(right_start, right_start       + len(right.points)     + len(right_frame.points)),
            "bottom": (bottom_start, bottom_start   + len(bottom.points)    + len(bottom_frame.points)),
        }
        clouds[make_key(theta, rho)] = full_panel

        # Randomly perturb the main component (pc2)
        # Generate random rotations up to 5 degrees in each axis
        max_rotation = 5  # degrees
        rx = random.uniform(-max_rotation, max_rotation) * math.pi / 180
        ry = random.uniform(-max_rotation, max_rotation) * math.pi / 180
        rz = random.uniform(-max_rotation, max_rotation) * math.pi / 180
        
        # Create rotation matrix using Open3D
        R = o3d.geometry.get_rotation_matrix_from_xyz((rx, ry, rz))
        
        # Get the center of the point cloud to rotate around
        center = full_panel.get_center()
        
        # Rotate pc2 around its center
        full_panel.rotate(R, center=center)

        # Generate random translations in each axis
        max_translation = 0.25
        tx = random.uniform(-max_translation, max_translation)
        ty = random.uniform(-max_translation, max_translation)
        tz = random.uniform(-max_translation, max_translation)
        
        # Translate pc2
        full_panel.translate((tx, ty, tz))

        write_point_cloud(full_panel, f"{folder}/panel_{theta}_{rho}.ply", color=[1, 0, 0])

    with open("/home/luke/Documents/xmas2/cracked_overlaps.pkl", "wb") as f:
        pickle.dump(overlaps, f)

if __name__ == "__main__":
    main()