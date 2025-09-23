import numpy as np
from scipy.spatial.transform import Rotation, Slerp

def interpolate_similarity_transform(
    start_scale, start_quat, start_translation,
    end_scale, end_quat, end_translation, t
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
    t = np.clip(t, 0.0, 1.0)

    # 1. Linear interpolation for scale
    current_scale = (1 - t) * start_scale + t * end_scale
    
    # 2. Linear interpolation for translation
    current_translation = (1 - t) * start_translation + t * end_translation

    # 3. Spherical linear interpolation for the quaternion
    key_rots = Rotation.from_quat([start_quat, end_quat])
    slerp = Slerp([0, 1], key_rots)
    current_quat = slerp(t).as_quat()
    
    return current_scale, current_quat, current_translation

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

# def scale_quat_trans_to_matrix(scale, quaternion, translation):
#     """
#     Converts scale, quaternion, and translation to a 4x4 similarity matrix.

#     Args:
#         scale (float): The uniform scale factor.
#         quaternion (np.ndarray): The quaternion for rotation.
#         translation (np.ndarray): The translation vector.

#     Returns:
#         np.ndarray: The resulting 4x4 transformation matrix.
#     """
#     matrix = np.eye(4)
#     # Create the rotation matrix, apply scale, and place in the 4x4 matrix
#     rotation_matrix = Rotation.from_quat(quaternion).as_matrix()
#     matrix[:3, :3] = rotation_matrix * scale
#     matrix[:3, 3] = translation
    
#     return matrix

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

# --- Helper functions from previous discussions ---

def quat_trans_to_matrix(translation, quaternion):
    """Converts a rigid pose to a 4x4 matrix."""
    matrix = np.eye(4)
    matrix[:3, :3] = Rotation.from_quat(quaternion).as_matrix()
    matrix[:3, 3] = translation
    return matrix

def scale_quat_trans_to_matrix(scale, quaternion, translation):
    """Converts a similarity transform to a 4x4 matrix."""
    matrix = np.eye(4)
    rotation_matrix = Rotation.from_quat(quaternion).as_matrix()
    matrix[:3, :3] = rotation_matrix * scale
    matrix[:3, 3] = translation
    return matrix

# --- New function for your specific use case ---

def apply_similarity_to_rigid_pose(
    pose_quat, pose_translation,
    transform_scale, transform_quat, transform_translation
):
    """
    Applies a similarity transform to a rigid pose and returns a rigid pose.

    The scale of the similarity transform is "baked" into the final translation,
    and the final rotation is normalized.

    Args:
        pose_quat (np.ndarray): The initial quaternion of the rigid pose.
        pose_translation (np.ndarray): The initial translation of the rigid pose.
        transform_scale (float): The scale of the similarity transformation.
        transform_quat (np.ndarray): The quaternion of the similarity transformation.
        transform_translation (np.ndarray): The translation of the similarity transformation.

    Returns:
        tuple: The final (translation, quaternion) for the new rigid pose.
    """
    # 1. Convert the initial rigid pose (scale=1) to a matrix
    m_pose_rigid = quat_trans_to_matrix(pose_translation, pose_quat)
    
    # 2. Convert the similarity transformation to a matrix
    m_transform_similarity = scale_quat_trans_to_matrix(
        transform_scale, transform_quat, transform_translation
    )
    
    # 3. Apply the transformation
    m_final_similarity = m_pose_rigid @ m_transform_similarity
    
    # 4. Decompose the result back into a rigid format
    
    # The final translation includes the baked-in scale
    final_translation = m_final_similarity[:3, 3]
    
    # For the rotation, we must normalize out the scale
    scaled_rotation_matrix = m_final_similarity[:3, :3]
    # The new scale is the norm of any column vector
    final_scale = np.linalg.norm(scaled_rotation_matrix[:, 0])
    
    if np.isclose(final_scale, 0):
        # If scale is zero, rotation is undefined. Return identity.
        final_quat = np.array([0., 0., 0., 1.])
    else:
        # Divide by the scale to get a pure rotation matrix
        pure_rotation_matrix = scaled_rotation_matrix / final_scale
        final_quat = Rotation.from_matrix(pure_rotation_matrix).as_quat()
        
    return final_translation, final_quat