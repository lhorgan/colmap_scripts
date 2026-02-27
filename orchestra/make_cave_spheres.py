from cluster_points import cluster_points
import open3d as o3d
import numpy as np
import math
import os

from util import write_point_cloud, copy_img

# arr must be sorted lowest to highest
def get_closest_timestamp(goal, timestamps):
    for i in range(len(timestamps)):
        if timestamps[i] == goal:
            return i
        elif timestamps[i] > goal:
            prev = -math.inf
            if i > 0:
                prev = timestamps[i-1]
            if (goal - prev) < (timestamps[i] - goal):
                return i - 1
            return i
    return len(timestamps) - 1

def make_spheres(svin_path, images_path, dst_path):
    svin_points = []
    svin_timestamps = []

    with open(svin_path) as f:
        for line in f.readlines():
            if line.startswith("#"):
                continue
            timestamp, tx, ty, tz, qx, qy, qz, qw = line.split(" ")
            timestamp = int(timestamp.replace(".", ""))

            tx = float(tx)
            ty = float(ty)
            tz = float(tz)

            svin_points.append([tx, ty, tz])
            svin_timestamps.append(timestamp)
    
    image_names = os.listdir(images_path)
    points = []
    timestamps = []

    print("Finding closest temporal matches")
    for image_name in image_names:
        timestamp = int(image_name.split(".")[0])
        closest_index = get_closest_timestamp(timestamp, svin_timestamps)
        
        closest_point = svin_points[closest_index]
        closest_timestamp = svin_timestamps[closest_index]

        points.append(closest_point)
        timestamps.append(timestamp)

    print("Assigning clusters")
    num_clusters = 70
    memberships, centers = cluster_points(
        points=points,
        num_clusters=num_clusters,
        expansion=0.3
    )

    point_clusters = [[] for i in range(num_clusters)]
    image_clusters = [[] for i in range(num_clusters)]

    for i, point in enumerate(points):
        membership = memberships[i]
        image_name = str(timestamps[i])#.replace(".", "")

        for j in membership:
            point_clusters[j].append(point)
            image_clusters[j].append(image_name)
    
    print("SET SIZE", len(set(timestamps)))
    print("LIST SIZE", len(timestamps))
    for i, cluster in enumerate(point_clusters):
        print(f"cluster {i} has {len(image_clusters[i])} points")
    for i, cluster in enumerate(point_clusters):
        print(f"IMAGES FOR CLUSTER {i}")
        pcd = o3d.geometry.PointCloud()

        for image_name in image_clusters[i]:
            print(image_name)
            copy_img(f"{images_path}/{image_name}.png", dst_path=f"{dst_path}/cluster_{i}/Images/{image_name}.png")
        
        print("\n\n")

        pcd.points = o3d.utility.Vector3dVector(np.array(cluster))
        write_point_cloud(pcd, f"{dst_path}/cluster_{i}/cluster_{i}.ply")
        

make_spheres(svin_path="/mnt/disk_1_ssd/luke/blub/svin_raw/center.txt",
             images_path="/mnt/disk_1_ssd/luke/blub/Combined/Images",
             dst_path="/mnt/disk_1_ssd/luke/blub/spheres")