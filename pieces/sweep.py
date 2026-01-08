import open3d as o3d
import numpy as np

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

def read_point_cloud(file_path):
    """Read a point cloud from file"""
    return o3d.io.read_point_cloud(file_path)