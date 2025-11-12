import open3d as o3d
import numpy as np
import os
import pickle

def read_point_cloud(file_path):
    """Read a point cloud from file"""
    return o3d.io.read_point_cloud(file_path)

def write_point_cloud(point_cloud, file_path):
    """Write the point cloud to the file path specified"""
    o3d.io.write_point_cloud(file_path, point_cloud)

def make_combined_cloud(root):
    print(root)
    pcd_filenames = os.listdir(root)
    pcd_filenames.sort(key=lambda pcd_name: int(pcd_name.split("_")[1][:-4]))

    pcds = []
    pcd_names = []

    combined_pcd = o3d.geometry.PointCloud()

    for pcd_filename in pcd_filenames:
        pcd_path = f"{root}/{pcd_filename}"
        pcd = read_point_cloud(pcd_path)

        pcds.append(pcd)
        
        pcd_names.append(int(pcd_filename[:-4].split("_")[1]))

        distances = pcd.compute_nearest_neighbor_distance()
        avg_distance = np.mean(distances)

        #print(avg_distance)

    for pcd in pcds:
        combined_pcd += pcd
    
    bounds = combined_pcd.get_max_bound() - pcd.get_min_bound()
    diag = np.linalg.norm(bounds)
    print("DIAG is ", diag)

    pcd_ids = np.ones(len(combined_pcd.points)).astype("uint16")
    start = 0
    for i in range(len(pcds)):
        pcd = pcds[i]
        pcd_ids[start:start+len(pcd.points)] = i
        start += len(pcd.points)

    print("Building PCD tree")
    neighboring_clouds = [{} for i in range(len(pcds))]

    pcd_tree = o3d.geometry.KDTreeFlann(combined_pcd)
    for i in range(len(combined_pcd.points)):
        if i % 1000 == 0:
            print(i)

        curr_cloud_id = int(pcd_ids[i])
        query_point = combined_pcd.points[i]
        [k, idx, _] = pcd_tree.search_radius_vector_3d(query_point, 0.2)
        idx = np.array(idx)
        cloud_ids_for_nearby_points = pcd_ids[idx]
        idxs_for_cloud_ids_in_other_point_clouds = np.where(cloud_ids_for_nearby_points != curr_cloud_id)[0]
        #print(idxs_for_cloud_ids_in_other_point_clouds.shape)
        point_idxs_for_points_in_other_clouds = idx[idxs_for_cloud_ids_in_other_point_clouds]
        #print(point_idxs_for_points_in_other_clouds)
        for point_idx_in_other_cloud in point_idxs_for_points_in_other_clouds:
            pcd_id = int(pcd_ids[point_idx_in_other_cloud])
            if pcd_id not in neighboring_clouds[curr_cloud_id]:
                #print(f"{pcd_id} is not in neighboring_clouds[{curr_cloud_id}]")
                neighboring_clouds[curr_cloud_id][pcd_id] = set()
            neighboring_clouds[curr_cloud_id][pcd_id].add(point_idx_in_other_cloud)

    for i in range(len(pcds)):
        neighbors = neighboring_clouds[i]
        print(neighbors)
        for neighbor_id in neighbors:
            point_ids = list(neighbors[neighbor_id])
            nearby_cloud = combined_pcd.select_by_index(point_ids)
            neighbor_path = "/home/luke/xmas/Neighbors2"
            write_point_cloud(nearby_cloud, f"{neighbor_path}/{pcd_names[neighbor_id]}_close_to_{pcd_names[i]}.ply")
    # with open("nearby_clouds.pkl", "wb+") as f:
    #     pickle.dump(neighboring_clouds, f)

    #point_counts = np.array(point_counts)

    # print(np.mean(point_counts))
    # print(np.sum(point_counts))
    # print(np.std(point_counts))

    #return np.sum(point_counts)


def main():
    make_combined_cloud("/home/luke/xmas/AlignedCubes")

if __name__ == "__main__":
    main()