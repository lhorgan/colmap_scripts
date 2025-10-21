import numpy as np
from scipy.spatial.transform import Rotation

def kabsch_umeyama(A, B):
    assert A.shape == B.shape
    n, m = A.shape

    EA = np.mean(A, axis=0)
    EB = np.mean(B, axis=0)
    VarA = np.mean(np.linalg.norm(A - EA, axis=1) ** 2)

    H = ((A - EA).T @ (B - EB)) / n
    U, D, VT = np.linalg.svd(H)
    d = np.sign(np.linalg.det(U) * np.linalg.det(VT))
    S = np.diag([1] * (m - 1) + [d])

    R = U @ S @ VT
    c = VarA / np.trace(np.diag(D) @ S)
    t = EA - c * R @ EB

    return R, c, t

def get_homography_matrix(A, B):
    R, c, t = kabsch_umeyama(A, B)
    M = np.empty((4, 4))
    M[:3, :3] = R*c
    M[:3, 3] = t
    M[3, :] = [0, 0, 0, 1]
    return M

def create_pose_matrix(tx, ty, tz, qx, qy, qz, qw):
    """Create 4x4 pose matrix from translation and quaternion"""
    P = np.eye(4)
    
    # Set rotation part (3x3)
    #P[:3,:3] = Rotation.from_quat([qx, qy, qz, qw])
    r = Rotation.from_quat([qx, qy, qz, qw]).as_matrix()
    #print(r)
    P[:3,:3] = r
    
    # Set translation part (3x1)
    P[:3,3] = [tx, ty, tz]
    
    return P

def create_pose_quat(M):
    R = M[:3, :3]
    t = M[:3, 3]
    q = Rotation.from_matrix(R).as_quat()
    return q, t 

def get_corresponding_poses(svin_path, svin_from_colmap_path):
        image_name_to_colmap_pose = {}
        image_name_to_svin_pose = {}

        # Cam poses from COLMAP must be inverted!
        with open(svin_from_colmap_path) as f:
            for line in f:
                if line.startswith("#"):
                        continue
                    
                line = line.rstrip()
                timestamp = line.split(" ")[0]
                tx, ty, tz, qx, qy, qz, qw = [float(f) for f in line.split(" ")[1:]]
                image_name = f"{timestamp.replace('.', '')}.png"
                
                pose_matrix = create_pose_matrix(tx, ty, tz, qx, qy, qz, qw)
                image_name_to_svin_pose[image_name] = pose_matrix

        # SVIN poses must not be inverted
        with open(svin_path) as f:
            for line in f:
                if line.startswith("#"):
                    continue
                
                line = line.rstrip()
                #timestamp tx ty tz qx qy qz qw
                timestamp = line.split(" ")[0]
                tx, ty, tz, qx, qy, qz, qw = [float(f) for f in line.split(" ")[1:]]
                image_name = f"{timestamp.replace('.', '')}.png"

                pose_matrix = create_pose_matrix(tx, ty, tz, qx, qy, qz, qw)
                image_name_to_colmap_pose[image_name] = pose_matrix

        svin_poses = []
        colmap_poses = []
        for image_name in image_name_to_colmap_pose:
             if image_name in image_name_to_svin_pose:
                svin_poses.append(image_name_to_svin_pose[image_name])
                colmap_poses.append(image_name_to_colmap_pose[image_name])
        
        svin_poses = np.array(svin_poses)
        colmap_poses = np.array(colmap_poses)

        #print(len(svin_poses), len(colmap_poses))

        return svin_poses, colmap_poses

# https://gemini.google.com/app/051b947ae58f1d0b, helpful chat, didn't write the code
def compute_alignment_stats(scene):
    data_path = "/mnt/Data3/luke/xmas/MergedCubes"
    #scene = "bin_0"
    svin_scaffold_path = "/mnt/Data3/luke/maindiskbackup/datasets/Right/svin_RightOnRig_Depth_introduced_par_det_transform_only_7x5.txt"
    svin_from_colmap_inv_path = f"{data_path}/{scene}/svin_from_colmap_inv.txt"

    svin_poses, colmap_poses = get_corresponding_poses(svin_scaffold_path, svin_from_colmap_inv_path)
    if len(svin_poses) == 0:
        return
    
    print(f"Computing stats for {scene}")

    transforms = np.zeros((len(svin_poses), 7))
    for i in range(len(svin_poses)):
        A = colmap_poses[i]
        B = svin_poses[i]

        A_inv = np.linalg.inv(A)
        A_to_B = A_inv @ B

        #print(A @ A_to_B) # Should give back B

        q, t = create_pose_quat(A_to_B)
        transforms[i] = np.concatenate((q, t))

    components = ["qx", "qy", "qz", "qw", "tx", "ty", "tz"]
    print("comp\t\tmean\t\tstd")
    for i in range(len(components)):
        col = transforms[:,i]
        print(f"{components[i]}\t\t{np.mean(col):.3f}\t\t{np.std(col):.4f}")
    
    print("\n")

def go():
    import os

    cube_dirs = os.listdir("/mnt/Data3/luke/xmas/MergedCubes")
    cube_dirs.sort(key=lambda dirname: int(dirname.split("_")[1]))

    #print(cube_dirs)

    for scene in cube_dirs:
        try:
            compute_alignment_stats(scene)
        except:
            pass

go()