import numpy as np
import open3d as o3d

# Gemini
def apply_homography(points, homography):
    """
    Applies a 4x4 homography matrix to a list of 3D points.

    Args:
    points: A NumPy array of shape (N, 3) representing N points.
    homography: A 4x4 NumPy array representing the homography matrix.

    Returns:
    A NumPy array of shape (N, 3) with the transformed points.
    """
    # 1. Convert 3D points to 4D homogeneous coordinates by adding a '1'
    homogeneous_points = np.hstack((points, np.ones((points.shape[0], 1))))

    # 2. Apply the homography transformation (matrix multiplication)
    #    We transpose the homography to work with row vectors.
    transformed_homogeneous = homogeneous_points @ homography.T

    # 3. Convert back to 3D Cartesian coordinates by perspective division
    #    (dividing x, y, z by the new w coordinate)
    transformed_points = transformed_homogeneous[:, :3] / transformed_homogeneous[:, 3, np.newaxis]

    return transformed_points

def read_point_cloud(point_cloud_file: str):
    """Reads a point cloud from a file.

    Parameters:
    point_cloud_file: Input point cloud file.

    Returns:
    The point cloud as an NDArray stored in the given file.
    """
    cloud = o3d.io.read_point_cloud(point_cloud_file)
    return np.array(cloud.points), cloud.colors

def write_point_cloud_np(filename, points, colors=None):
    cloud = o3d.geometry.PointCloud()
    cloud.points = o3d.utility.Vector3dVector(points)
    if colors is not None:
        cloud.colors = o3d.utility.Vector3dVector(colors)
    o3d.io.write_point_cloud(filename, cloud)