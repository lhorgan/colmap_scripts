import open3d as o3d

def read_point_cloud(file_path):
    """Read a point cloud from file"""
    return o3d.io.read_point_cloud(file_path)

def write_point_cloud(point_cloud, file_path):
    """Write the point cloud to the file path specified"""
    o3d.io.write_point_cloud(file_path, point_cloud)

def get_bounding_box(point_cloud):
    """Return the axis-aligned bounding box for the point cloud"""
    return point_cloud.get_axis_aligned_bounding_box()

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