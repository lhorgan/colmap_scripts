import numpy as np
import open3d as o3d

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

def auto_threshold(points, frac=0.001, floor=1e-6):
    # points: (N,3) ndarray
    # bbox diagonal length = norm(max - min)
    diag = np.linalg.norm(points.max(axis=0) - points.min(axis=0))
    return max(floor, frac * float(diag))

def as_legacy_pcd(x):
    if isinstance(x, o3d.geometry.PointCloud):
        return x
    pts = np.asarray(x)
    pcd = o3d.geometry.PointCloud()
    pcd.points = o3d.utility.Vector3dVector(pts)
    return pcd

def align_icp(tgt, src, initial_guess=np.eye(4)):
    estimation = o3d.pipelines.registration.TransformationEstimationPointToPoint()

    criteria = o3d.pipelines.registration.ICPConvergenceCriteria(max_iteration=50000)

    # Initial guess = identity (they're nearly aligned)
    init = initial_guess

    thresh = auto_threshold(tgt)
    
    print("src, dst", type(src), type(tgt))

    src = as_legacy_pcd(src)
    tgt = as_legacy_pcd(tgt)

    # Run ICP on working (optionally downsampled) clouds
    reg = o3d.pipelines.registration.registration_icp(
        src, tgt, thresh, init, estimation, criteria
    )

    T = reg.transformation
    R, t = T[:3, :3], T[:3, 3]

    # Apply transform to the full-resolution source and save
    src_aligned = src.transform(T.copy())

    # Report
    print("\n=== ICP Result ===")
    print(f"Fitness (inlier ratio): {reg.fitness:.6f}")
    print(f"RMSE: {reg.inlier_rmse:.6f}")
    print(f"Correspondence threshold: {thresh:.6f}")
    print("\nTransformation (source → target), 4x4 homogeneous:\n")
    np.set_printoptions(precision=6, suppress=True)
    print(T)
    print("\nRotation R (3x3):\n", R)
    print("\nTranslation t (3,):\n", t)

    return src_aligned, T

def geo_mean(coords):
    return np.array([np.mean(coords[:,0]), np.mean(coords[:,1]), np.mean(coords[:,2])])