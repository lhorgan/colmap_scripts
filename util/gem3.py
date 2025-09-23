import numpy as np
from scipy.spatial.transform import Rotation

# --- Helper Functions for Conversion ---

def scale_quat_trans_to_matrix(scale, quaternion, translation):
    """Converts a similarity transform's components to a 4x4 matrix."""
    matrix = np.eye(4)
    rotation_matrix = Rotation.from_quat(quaternion).as_matrix()
    matrix[:3, :3] = rotation_matrix * scale
    matrix[:3, 3] = translation
    return matrix

def rotmat_to_quat(R):
    """Converts a single 3x3 rotation matrix to a quaternion."""
    return Rotation.from_matrix(R).as_quat()

# --- The Core Function You Need ---

def apply_transform_from_script(transform_matrix, pose_center, pose_rotation_matrix):
    """
    Applies a similarity transform to a single pose using the exact logic
    from the provided script.

    Args:
        transform_matrix (np.ndarray): The 4x4 similarity transform matrix to apply.
        pose_center (np.ndarray): The initial 3D translation/center of the pose.
        pose_rotation_matrix (np.ndarray): The initial 3x3 rotation matrix of the pose.

    Returns:
        tuple: A tuple containing:
            - final_center (np.ndarray): The new 3D center.
            - final_rotation_matrix (np.ndarray): The new 3x3 rotation matrix.
    """
    T = np.asarray(transform_matrix, dtype=np.float64)
    C = np.asarray(pose_center, dtype=np.float64)
    R = np.asarray(pose_rotation_matrix, dtype=np.float64)

    # 1. Extract components from the 4x4 transform matrix
    R_T = T[:3, :3]
    t_T = T[:3, 3]

    # 2. Transform the center point (This is line 232 from your script)
    # C_new = C @ R_T.T + t_T
    # Note: The script uses the transpose R_T.T because it treats C as a row vector.
    # The math is equivalent to R_T @ C if C were a column vector.
    C_new = C @ R_T.T + t_T

    # 3. Transform the rotation matrix (This is line 235 from your script)
    R_new = R_T @ R

    # 4. Re-project the new rotation matrix to SO(3) to remove scale/skew
    # (This is the SVD part from lines 238-245 of your script)
    U, _, Vt = np.linalg.svd(R_new)
    R_new_reprojected = U @ Vt
    # Fix potential reflections
    if np.linalg.det(R_new_reprojected) < 0:
        U[:, -1] *= -1.0
        R_new_reprojected = U @ Vt

    return C_new, R_new_reprojected

import numpy as np
from scipy.spatial.transform import Rotation

def apply_similarity_transform(
    pose_translation: np.ndarray,
    pose_quaternion: np.ndarray,
    transform_scale: float,
    transform_quaternion: np.ndarray,
    transform_translation: np.ndarray
) -> tuple[np.ndarray, np.ndarray]:
    """
    Applies a similarity transform to a rigid pose and returns the new rigid pose.

    This function uses the exact transformation logic found in your trusted script,
    ensuring consistent results. The scale is "baked" into the final translation.

    Args:
        pose_translation: The initial 3D translation vector [x, y, z].
        pose_quaternion: The initial quaternion [x, y, z, w].
        transform_scale: The scale factor of the transformation to apply.
        transform_quaternion: The quaternion of the transformation.
        transform_translation: The translation vector of the transformation.

    Returns:
        A tuple containing the final translation and final quaternion.
    """
    # --- 1. Convert all inputs to matrix format ---
    # Initial pose (rigid, so scale is 1.0)
    initial_pose_rotmat = Rotation.from_quat(pose_quaternion).as_matrix()
    
    # Similarity transform
    transform_rotmat = Rotation.from_quat(transform_quaternion).as_matrix()
    transform_4x4 = np.eye(4)
    transform_4x4[:3, :3] = transform_rotmat * transform_scale
    transform_4x4[:3, 3] = transform_translation

    # --- 2. Apply the core transformation logic from your script ---
    # Extract components from the 4x4 transform matrix
    R_T = transform_4x4[:3, :3]
    t_T = transform_4x4[:3, 3]

    # Transform the center point
    final_translation = pose_translation @ R_T.T + t_T

    # Transform the rotation matrix
    R_new = R_T @ initial_pose_rotmat

    # Re-project to the closest pure rotation matrix (removes scale) via SVD
    U, _, Vt = np.linalg.svd(R_new)
    final_rotation_matrix = U @ Vt
    # Fix potential reflections to ensure it's a proper rotation
    if np.linalg.det(final_rotation_matrix) < 0:
        U[:, -1] *= -1.0
        final_rotation_matrix = U @ Vt

    # --- 3. Convert the final rotation matrix back to a quaternion ---
    final_quaternion = Rotation.from_matrix(final_rotation_matrix).as_quat()

    return final_translation, final_quaternion