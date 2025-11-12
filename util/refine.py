import open3d as o3d
import numpy as np
import os

def read_point_cloud(file_path):
    """Read a point cloud from file"""
    return o3d.io.read_point_cloud(file_path)

def write_point_cloud(point_cloud, file_path, color=None):
    if len(point_cloud.points) == 0:
        return
    """Write the point cloud to the file path specified
    
    Args:
        point_cloud: Open3D point cloud object
        file_path: Path where the point cloud will be saved
        color: Optional RGB color tuple/list (values between 0 and 1), 
               e.g., (1.0, 0.0, 0.0) for red
    """
    if color is not None:
        # Create an array of colors, one for each point
        num_points = len(point_cloud.points)
        colors = np.tile(color, (num_points, 1))
        point_cloud.colors = o3d.utility.Vector3dVector(colors)
    
    o3d.io.write_point_cloud(file_path, point_cloud)

def get_bounding_box(point_cloud):
    """Return the axis-aligned bounding box for the point cloud"""
    return point_cloud.get_axis_aligned_bounding_box()

def get_overlap(box1, box2):
    #print(box1)
    #print(box2)

    min_bounds = np.max(np.array([[box1.min_bound, box2.min_bound]]), axis=1)
    max_bounds = np.min(np.array([[box1.max_bound, box2.max_bound]]), axis=1)

    overlap_lens = max_bounds - min_bounds

    if np.min(overlap_lens) < 0:
        return 0, 0

    vol = np.prod(overlap_lens)

    smaller_box = box1
    if box2.volume() < box1.volume():
        smaller_box = box2

    return vol, vol / smaller_box.volume()

def auto_threshold(pcd):
    # Use 1% of the target's bounding-box diagonal as a sensible default
    bounds = pcd.get_max_bound() - pcd.get_min_bound()
    diag = np.linalg.norm(bounds)
    return max(1e-6, 0.01 * diag)

# def align_point_clouds_icp(pc1, pc2):
#     """Align pc2 to pc1 using ICP with better parameters"""
#     threshold = 0.1
    
#     reg_result = o3d.pipelines.registration.registration_icp(
#         pc2, pc1, threshold,
#         estimation_method=o3d.pipelines.registration.TransformationEstimationPointToPoint(),
#         criteria=o3d.pipelines.registration.ICPConvergenceCriteria(max_iteration=1000)
#     )
    
#     pc2_aligned = pc2.transform(reg_result.transformation)
#     return pc2_aligned
def align_point_clouds_icp(pc1, pc2):
    """Align pc2 to pc1 using point-to-plane ICP"""
    # Estimate normals (needed for point-to-plane)
    pc1.estimate_normals(search_param=o3d.geometry.KDTreeSearchParamHybrid(radius=0.1, max_nn=30))
    pc2.estimate_normals(search_param=o3d.geometry.KDTreeSearchParamHybrid(radius=0.1, max_nn=30))
    
    threshold = 0.1
    reg_result = o3d.pipelines.registration.registration_icp(
        pc2, pc1, threshold,
        criteria=o3d.pipelines.registration.ICPConvergenceCriteria(max_iteration=1000),
        estimation_method=o3d.pipelines.registration.TransformationEstimationPointToPlane()
    )
    
    print(reg_result.transformation)

    pc2_aligned = pc2.transform(reg_result.transformation)
    return pc2_aligned

def get_transform_icp(pc1, pc2):
    """Align pc2 to pc1 using point-to-plane ICP"""
    # Estimate normals (needed for point-to-plane)
    pc1.estimate_normals(search_param=o3d.geometry.KDTreeSearchParamHybrid(radius=0.1, max_nn=30))
    pc2.estimate_normals(search_param=o3d.geometry.KDTreeSearchParamHybrid(radius=0.1, max_nn=30))
    
    threshold = 0.1
    reg_result = o3d.pipelines.registration.registration_icp(
        pc2, pc1, threshold,
        criteria=o3d.pipelines.registration.ICPConvergenceCriteria(max_iteration=1000),
        estimation_method=o3d.pipelines.registration.TransformationEstimationPointToPlane()
    )
    
    return reg_result.transformation

def remove_outliers_statistical(point_cloud, nb_neighbors=20, std_ratio=2.0):
    """Remove statistical outliers from point cloud"""
    cl, ind = point_cloud.remove_statistical_outlier(
        nb_neighbors=nb_neighbors,
        std_ratio=std_ratio
    )
    return cl  # Returns cleaned point cloud

def test_overlap(root):
    pc_names = os.listdir(root)
    pc_names.sort(key=lambda pc_name: int(pc_name.split("_")[1][:-4]))

    pcs = []
    for pc_name in pc_names:
        pc_path = f"{root}/{pc_name}"
        pc = read_point_cloud(pc_path)
        pc_clean = remove_outliers_statistical(pc, nb_neighbors=10, std_ratio=2)
        if len(pc_clean.points) > 500:
            pcs.append(pc_clean)
    
    for i in range(len(pcs)):
        print("Computing overlaps for ", pc_names[i])
        box1 = get_bounding_box(pcs[i])
        for j in range(len(pcs)):
            if i == j:
                continue
            box2 = get_bounding_box(pcs[j])
            overlap_vol, overlap_perc = get_overlap(box1, box2)
            if overlap_perc > 0.5:
                print(f"{pc_names[j]} overlaps bin {pc_names[i]} at {overlap_perc}.")
                aligned = align_point_clouds_icp(pcs[i], pcs[j])
                write_point_cloud(aligned, f"/home/luke/xmas/refined_cubes/{pc_names[j]}_to_{pc_names[i]}.ply")

        break

def main():
    # pc1 = read_point_cloud("/home/luke/xmas/AlignedCubes/bin_0.ply")
    # pc2 = read_point_cloud("/home/luke/xmas/AlignedCubes/bin_130.ply")
    # box1 = get_bounding_box(pc1)
    # box2 = get_bounding_box(pc2)
    # overlap_area, overlap_perc = get_overlap(box1, box2)
    # print(overlap_area, overlap_perc)
    test_overlap("/home/luke/xmas/AlignedCubes")

if __name__ == "__main__":
    main()