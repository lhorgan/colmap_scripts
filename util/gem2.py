import numpy as np
from scipy.spatial.transform import Rotation, Slerp

def interpolate_similarity_transform(
    start_scale, start_translation, start_quat,
    end_scale, end_translation, end_quat, t
):
    """
    Smoothly interpolates/extrapolates between two similarity transformations.

    Args:
        start_scale (float): The starting scale factor.
        start_translation (np.ndarray): The starting translation vector.
        start_quat (np.ndarray): The starting quaternion.
        end_scale (float): The ending scale factor.
        end_translation (np.ndarray): The ending translation vector.
        end_quat (np.ndarray): The ending quaternion.
        t (float): The interpolation/extrapolation factor.

    Returns:
        tuple: The interpolated (scale, translation, quaternion).
    """
    # 1. Linear interpolation for scale
    current_scale = (1 - t) * start_scale + t * end_scale
    
    # 2. Linear interpolation for translation
    current_translation = (1 - t) * start_translation + t * end_translation

    # 3. Spherical linear interpolation for the quaternion
    key_rots = Rotation.from_quat([start_quat, end_quat])
    slerp = Slerp([0, 1], key_rots)
    current_quat = slerp(t).as_quat()
    
    return current_scale, current_translation, current_quat

def matrix_to_scale_quat_trans(matrix):
    """
    Decomposes a 4x4 similarity matrix into scale, quaternion, and translation.

    Args:
        matrix (np.ndarray): The 4x4 transformation matrix.

    Returns:
        tuple: (scale, quaternion, translation).
    """
    translation = matrix[:3, 3]
    # The scale is the norm (length) of one of the column vectors
    scale = np.linalg.norm(matrix[:3, 0])
    if np.isclose(scale, 0):
        raise ValueError("Matrix has zero scale; rotation is undefined.")
    
    # Remove scale to get the pure rotation matrix
    rotation_matrix = matrix[:3, :3] / scale
    quaternion = Rotation.from_matrix(rotation_matrix).as_quat()
    
    return scale, quaternion, translation

def scale_quat_trans_to_matrix(scale, quaternion, translation):
    """
    Converts scale, quaternion, and translation to a 4x4 similarity matrix.

    Args:
        scale (float): The uniform scale factor.
        quaternion (np.ndarray): The quaternion for rotation.
        translation (np.ndarray): The translation vector.

    Returns:
        np.ndarray: The resulting 4x4 transformation matrix.
    """
    matrix = np.eye(4)
    # Create the rotation matrix, apply scale, and place in the 4x4 matrix
    rotation_matrix = Rotation.from_quat(quaternion).as_matrix()
    matrix[:3, :3] = rotation_matrix * scale
    matrix[:3, 3] = translation
    
    return matrix

def apply_similarity_transform_with_matrices(
    pose_scale, pose_quat, pose_translation,
    transform_scale, transform_quat, transform_translation
):
    """
    Applies a similarity transformation to a pose using 4x4 matrix multiplication.

    Args:
        pose_scale (float): The initial scale.
        pose_quat (np.ndarray): The initial quaternion.
        pose_translation (np.ndarray): The initial translation.
        transform_scale (float): The scale of the transformation to apply.
        transform_quat (np.ndarray): The quaternion of the transformation to apply.
        transform_translation (np.ndarray): The translation of the transformation to apply.

    Returns:
        tuple: The final (scale, quaternion, translation) of the new pose.
    """
    # 1. Convert the initial pose to a matrix
    m_pose = scale_quat_trans_to_matrix(pose_scale, pose_quat, pose_translation)
    
    # 2. Convert the transformation to a matrix
    m_transform = scale_quat_trans_to_matrix(transform_scale, transform_quat, transform_translation)
    
    # 3. Apply the transformation via matrix multiplication
    m_new = m_pose @ m_transform
    
    # 4. Convert the resulting matrix back to its components
    final_scale, final_quat, final_trans = matrix_to_scale_quat_trans(m_new)
    
    return final_scale, final_quat, final_trans