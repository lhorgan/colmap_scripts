import open3d as o3d
import numpy as np

def read_point_cloud(file_path):
    """Read a point cloud from file"""
    return o3d.io.read_point_cloud(file_path)

def write_point_cloud(point_cloud, file_path):
    """Write the point cloud to the file path specified"""
    o3d.io.write_point_cloud(file_path, point_cloud)

def get_bounding_box(point_cloud):
    """Return the axis-aligned bounding box for the point cloud"""
    return point_cloud.get_axis_aligned_bounding_box()

def get_overlap(box1, box2):
    # print("Min bounds")
    # print(box1.min_bound)
    # print(box2.min_bound)
    # print("\n")

    # print("Max bounds")
    # print(box1.max_bound)
    # print(box2.max_bound)
    # print("\n")

    min_bounds = np.max(np.array([[box1.min_bound, box2.min_bound]]), axis=1)
    max_bounds = np.min(np.array([[box1.max_bound, box2.max_bound]]), axis=1)
    
    # print("Overlap bounds")
    # print(min_bounds)
    # print(max_bounds)
    # print("\n")

    overlap_lens = max_bounds - min_bounds
    # print("Diff")
    # print(overlap_lens)

    vol = np.prod(overlap_lens)

    larger_box = box1
    if box2.volume() > box1.volume():
        larger_box = box2

    return vol, vol / larger_box.volume()

def align_point_clouds_icp(pc1, pc2):
    """Align pc2 to pc1 using ICP and return the aligned version of pc2"""
    # Run ICP registration
    threshold = 0.02  # Maximum correspondence distance (adjust as needed)
    reg_result = o3d.pipelines.registration.registration_icp(
        pc2, pc1, threshold,
        estimation_method=o3d.pipelines.registration.TransformationEstimationPointToPoint()
    )
    
    # Transform pc2 with the computed transformation
    pc2_aligned = pc2.transform(reg_result.transformation)
    
    return pc2_aligned

def main():
    pc1 = read_point_cloud("/home/luke/xmas/AlignedCubes/bin_0.ply")
    pc2 = read_point_cloud("/home/luke/xmas/AlignedCubes/bin_1.ply")
    box1 = get_bounding_box(pc1)
    box2 = get_bounding_box(pc2)
    overlap_area, overlap_perc = get_overlap(box1, box2)
    print(overlap_area, overlap_perc)

if __name__ == "__main__":
    main()