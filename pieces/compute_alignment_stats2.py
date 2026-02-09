import numpy as np
from scipy.spatial.transform import Rotation
import matplotlib.pyplot as plt

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
                
                #pose_matrix = create_pose_matrix(tx, ty, tz, qx, qy, qz, qw)
                image_name_to_svin_pose[image_name] = [tx, ty, tz, qx, qy, qz, qw]#pose_matrix

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

                #pose_matrix = create_pose_matrix(tx, ty, tz, qx, qy, qz, qw)
                image_name_to_colmap_pose[image_name] = [tx, ty, tz, qx, qy, qz, qw]#pose_matrix

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
    

def compute_alignment_stats(scene):
    data_path = "/mnt/Data3/luke/xmas/MergedCubes"
    #scene = "bin_0"
    svin_scaffold_path = "/home/luke/Documents/titanic/svin_scaffold.txt"
    svin_from_colmap_inv_path = f"{data_path}/{scene}/svin_from_colmap_inv.txt"

    svin_poses, colmap_poses = get_corresponding_poses(svin_scaffold_path, svin_from_colmap_inv_path)

    if len(svin_poses) < 2:
        return

    svin_centers = [[p[0], p[1], p[2]] for p in svin_poses]
    colmap_centers = [[p[0], p[1], p[2]] for p in colmap_poses]

    #print(svin_centers.shape)

    print(f"Computing stats for {scene}, with {len(svin_centers)} centers.")

    A = np.array(svin_centers)
    B = np.array(colmap_centers)
    
    M = get_homography_matrix(A, B)

    errors = []
    for i in range(len(svin_poses)):
        svin_center = np.append(svin_centers[i], 1)
        colmap_center = np.append(colmap_centers[i], 1)
        colmap_center_p = M @ colmap_center
        error = np.abs(colmap_center_p - svin_center)
        errors.append(error)
        # svin_pose = svin_poses[i]
        # colmap_pose = colmap_poses[i]
        
        # svin_mat = create_pose_matrix(*svin_pose)
        # colmap_mat = create_pose_matrix(*colmap_pose)
        
        # colmap_mat_p = M @ colmap_mat

        # print(colmap_mat_p)
        # print(svin_mat)
        # print("\n")

    errors = np.array(errors)
    components = ["tx", "ty", "tz"]
    print("comp\t\tmean\t\tstd")
    for i in range(len(components)):
        col = errors[:,i]
        print(f"{components[i]}\t\t{np.mean(col):.3f}\t\t{np.std(col):.4f}")
    return errors
    #print(M)


def go():
    import os

    cube_dirs = os.listdir("/mnt/Data3/luke/xmas/MergedCubes")
    cube_dirs.sort(key=lambda dirname: int(dirname.split("_")[1]))

    #print(cube_dirs)

    categories = []
    exs = []
    eys = []
    ezs = []
    sxs = []
    sys = []
    szs = []
    for scene in cube_dirs:
        try:
            errors = compute_alignment_stats(scene)
            if errors is not None:
                categories.append(scene)
                exs.append(np.mean(errors[:,0]))
                eys.append(np.mean(errors[:,1]))
                ezs.append(np.mean(errors[:,2]))
                sxs.append(np.std(errors[:,0]))
                sys.append(np.std(errors[:,1]))
                szs.append(np.std(errors[:,2]))
        except:
            pass
    
    to_plots = [exs, eys, ezs, sxs, sys, szs]
    titles = ["ex", "ey", "ez", "sx", "sy", "sz"]
    for i in range(len(to_plots)):
        to_plot = to_plots[i]
        title = titles[i]
        plt.bar([c.split("_")[-1] for c in categories], to_plot)
        plt.ylim(bottom=0, top=1)
        plt.title(titles[i])
        plt.savefig(f"plots/{title}s.jpg")
        plt.show()
        #plt.clf()
        break
        #plt.show()

go()