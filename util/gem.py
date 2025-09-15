import numpy as np
from scipy.spatial.transform import Rotation, Slerp

def define_line_from_points(p1, p2):
    """
    Defines a 3D line from two points.

    Args:
        p1 (np.ndarray): The first 3D point (x, y, z).
        p2 (np.ndarray): The second 3D point (x, y, z).

    Returns:
        tuple: A tuple containing:
            - start_point (np.ndarray): The starting point of the line (p1).
            - direction_vector (np.ndarray): The normalized direction vector.
    """
    # The direction vector is the difference between the two points
    direction_vector = p2 - p1
    
    # Normalize the direction vector to have a unit length of 1
    norm = np.linalg.norm(direction_vector)
    if norm == 0:
        raise ValueError("The two points are identical; a line cannot be defined.")
    
    normalized_direction = direction_vector / norm
    
    return p1, normalized_direction

def project_point_onto_line(point, line_start, line_direction):
    """
    Projects an arbitrary 3D point onto a 3D line.

    Args:
        point (np.ndarray): The 3D point to project (x, y, z).
        line_start (np.ndarray): The starting point of the line.
        line_direction (np.ndarray): The normalized direction vector of the line.

    Returns:
        np.ndarray: The projected point on the line.
    """
    # Vector from the line's start point to the arbitrary point
    point_vector = point - line_start
    
    # The dot product gives the scalar projection of point_vector onto the line_direction.
    # Since line_direction is a unit vector, the magnitude is just the dot product.
    scalar_projection = np.dot(point_vector, line_direction)
    
    # The projected point is found by moving along the line's direction
    # from the start point by the distance of the scalar projection.
    projected_point = line_start + scalar_projection * line_direction
    
    return projected_point


def get_line_parameter(point_on_line, line_start, line_end):
    """
    Calculates the parametric value 't' for a point on a line segment.

    Args:
        point_on_line (np.ndarray): The point for which to find 't'.
        line_start (np.ndarray): The point corresponding to t=0.
        line_end (np.ndarray): The point corresponding to t=1.

    Returns:
        float: The parametric value 't'.
    """
    print("LA LA LA", line_start, line_end)

    # Vector defining the full segment (from t=0 to t=1)
    line_vec = line_end - line_start
    
    # Vector from the start of the segment to our point
    point_vec = point_on_line - line_start
    
    # The dot product of a vector with itself is its squared magnitude
    line_len_sq = np.dot(line_vec, line_vec)
    
    # If the points are the same, the line is undefined.
    if line_len_sq == 0:
        raise ValueError("Line start and end points cannot be the same.")
        
    # Project point_vec onto line_vec and normalize by the segment's length
    # This gives the value of 't'
    t = np.dot(point_vec, line_vec) / line_len_sq
    
    return t

def interpolate_transform(start_translation, start_quat, end_translation, end_quat, t):
    """
    Smoothly interpolates between two transformations (translation and quaternion).

    Args:
        start_translation (np.ndarray): The starting translation vector [x, y, z].
        start_quat (np.ndarray): The starting quaternion [x, y, z, w].
        end_translation (np.ndarray): The ending translation vector [x, y, z].
        end_quat (np.ndarray): The ending quaternion [x, y, z, w].
        t (float): The interpolation factor, clamped between 0.0 and 1.0.

    Returns:
        tuple: A tuple containing:
            - current_translation (np.ndarray): The interpolated translation vector.
            - current_quat (np.ndarray): The interpolated quaternion.
    """
    # 1. Clamp t to the valid range [0, 1]
    t = np.clip(t, 0.0, 1.0)

    # 2. Linear Interpolation (Lerp) for the translation vector
    current_translation = (1 - t) * start_translation + t * end_translation

    # 3. Spherical Linear Interpolation (Slerp) for the quaternion
    # Create Rotation objects from the quaternions
    key_rots = Rotation.from_quat([start_quat, end_quat])
    
    # Create a Slerp object
    slerp = Slerp([0, 1], key_rots)
    
    # Interpolate at time t
    interpolated_rotation = slerp(t)
    
    # Convert the resulting rotation object back to a quaternion
    current_quat = interpolated_rotation.as_quat()
    
    return current_translation, current_quat



def decompose_similarity_matrix(matrix):
    """
    Decomposes a 4x4 similarity transformation matrix into scale, rotation, and translation.

    Args:
        matrix (np.ndarray): The 4x4 similarity transformation matrix.

    Returns:
        tuple: A tuple containing:
            - scale (float): The uniform scale factor.
            - quaternion (np.ndarray): The rotation as a quaternion [x, y, z, w].
            - translation (np.ndarray): The translation vector [x, y, z].
    """
    # 1. Extract Translation
    translation = matrix[:3, 3]
    
    # 2. Extract Scale
    # The scale is the norm of any of the first three column vectors.
    scale = np.linalg.norm(matrix[:3, 0])
    
    # Handle the case of a zero scale to avoid division by zero
    if scale == 0:
        raise ValueError("Matrix has zero scale; rotation is undefined.")
    
    # 3. Extract Rotation Matrix
    # Divide the 3x3 sub-matrix by the scale to get the pure rotation
    rotation_matrix = matrix[:3, :3] / scale
    
    # 4. Convert to Quaternion
    r = Rotation.from_matrix(rotation_matrix)
    quaternion = r.as_quat()
    
    return scale, quaternion, translation

def matrix_to_quat_trans(matrix):
    """
    Converts a 4x4 homogeneous transformation matrix to a translation vector and a quaternion.

    Args:
        matrix (np.ndarray): The 4x4 transformation matrix.

    Returns:
        tuple: A tuple containing:
            - translation (np.ndarray): The translation vector [x, y, z].
            - quaternion (np.ndarray): The quaternion [x, y, z, w].
    """
    # Extract the rotation part (upper-left 3x3 matrix)
    rotation_matrix = matrix[:3, :3]
    
    # Convert the rotation matrix to a quaternion
    r = Rotation.from_matrix(rotation_matrix)
    quaternion = r.as_quat()
    
    # Extract the translation part (first three elements of the last column)
    translation = matrix[:3, 3]
    
    return translation, quaternion

def quat_trans_to_matrix(translation, quaternion):
    """
    Converts a translation vector and a quaternion to a 4x4 homogeneous transformation matrix.

    Args:
        translation (np.ndarray): The translation vector [x, y, z].
        quaternion (np.ndarray): The quaternion [x, y, z, w].

    Returns:
        np.ndarray: The resulting 4x4 transformation matrix.
    """
    # Create a 4x4 identity matrix
    matrix = np.eye(4)
    
    # Create a Rotation object from the quaternion
    r = Rotation.from_quat(quaternion)
    
    # Convert the rotation to a 3x3 matrix and place it in the upper-left
    matrix[:3, :3] = r.as_matrix()
    
    # Place the translation vector in the last column
    matrix[:3, 3] = translation
    
    return matrix

def apply_transform_with_matrices(pose_translation, pose_quat, transform_translation, transform_quat):
    """
    Applies a transformation to a pose using 4x4 matrix multiplication.

    Args:
        pose_translation (np.ndarray): The initial translation of the camera.
        pose_quat (np.ndarray): The initial quaternion of the camera.
        transform_translation (np.ndarray): The translation to apply, in the camera's local frame.
        transform_quat (np.ndarray): The quaternion rotation to apply.

    Returns:
        tuple: The final translation and quaternion of the new pose.
    """
    # 1. Convert the initial pose to a matrix
    m_pose = quat_trans_to_matrix(pose_translation, pose_quat)
    
    # 2. Convert the transformation to a matrix
    m_transform = quat_trans_to_matrix(transform_translation, transform_quat)
    
    # 3. Apply the transformation via matrix multiplication. The order is crucial!
    m_new = m_pose @ m_transform # Using @ operator for matrix multiplication
    
    # 4. Convert the resulting matrix back to a translation and quaternion
    final_translation, final_quaternion = matrix_to_quat_trans(m_new)
    
    return final_translation, final_quaternion