from cluster_points import cluster_points
import open3d as o3d
import numpy as np

from plywood import write_point_cloud, copy_img

def make_spheres(svin_path, images_path, dst_path):
    points = []
    timestamps = []

    with open(svin_path) as f:
        for line in f.readlines():
            if line.startswith("#"):
                continue
            timestamp, tx, ty, tz, qx, qy, qz, qw = line.split(" ")
            
            tx = float(tx)
            ty = float(ty)
            tz = float(tz)

            points.append([tx, ty, tz])
            timestamps.append(timestamp)

    num_clusters = 60
    memberships, centers = cluster_points(
        points=points,
        num_clusters=num_clusters,
        expansion=0.2
    )

    point_clusters = [[] for i in range(num_clusters)]
    image_clusters = [[] for i in range(num_clusters)]

    for i, point in enumerate(points):
        membership = memberships[i]
        image_name = timestamps[i].replace(".", "")

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
        

make_spheres(svin_path="/home/luke/Documents/titanic/Combined/svin_orig.txt",
             images_path="/home/luke/Documents/titanic/Combined/Images",
             dst_path="/home/luke/Documents/titanic/spheres")