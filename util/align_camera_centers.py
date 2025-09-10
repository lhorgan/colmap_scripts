#!/usr/bin/env python3
"""
Align two sets of corresponding camera centers (PLY) with a robust similarity transform.

Input:
  - ply_vi:     PLY of visual-inertial camera centers (N points)
  - ply_colmap: PLY of COLMAP camera centers         (N points)
Assumption: i-th point in ply_vi corresponds to i-th point in ply_colmap.

Method:
  - RANSAC over 3-point minimal sets
  - Model: Umeyama/Kabsch closed-form (optionally with scale)
  - Final refinement on inliers
Outputs:
  - 4x4 transform (from VI -> COLMAP)
  - Inlier stats and RMSE
  - Optional save of matrix/aligned cloud
"""

import argparse
import os
import sys
import numpy as np
import random

# Optional readers: try Open3D, then plyfile; fall back to a tiny ASCII PLY reader.
def load_points_from_ply(path):
    # Try Open3D
    try:
        import open3d as o3d
        pcd = o3d.io.read_point_cloud(path)
        pts = np.asarray(pcd.points, dtype=np.float64)
        if pts.size == 0:
            raise ValueError("No points in PLY (Open3D).")
        return pts
    except Exception:
        pass
    # Try plyfile
    try:
        from plyfile import PlyData
        ply = PlyData.read(path)
        v = ply["vertex"].data
        pts = np.vstack([v["x"], v["y"], v["z"]]).T.astype(np.float64)
        if pts.size == 0:
            raise ValueError("No points in PLY (plyfile).")
        return pts
    except Exception:
        pass
    # Minimal ASCII PLY (x y z as first three props)
    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        line = f.readline().strip()
        if line != "ply":
            raise RuntimeError("Not a PLY file and no reader available.")
        n_vertices = None
        is_ascii = True
        # Parse header
        while True:
            line = f.readline()
            if not line:
                raise RuntimeError("Unexpected EOF in PLY header.")
            line = line.strip()
            if line.startswith("format"):
                if "binary" in line:
                    is_ascii = False
            if line.startswith("element vertex"):
                n_vertices = int(line.split()[-1])
            if line == "end_header":
                break
        if not is_ascii:
            raise RuntimeError("Binary PLY not supported by fallback reader. Install open3d or plyfile.")
        pts = []
        for _ in range(n_vertices if n_vertices is not None else 10**9):
            line = f.readline()
            if not line:
                break
            toks = line.strip().split()
            if len(toks) < 3:
                continue
            try:
                pts.append([float(toks[0]), float(toks[1]), float(toks[2])])
            except ValueError:
                continue
        pts = np.asarray(pts, dtype=np.float64)
        if pts.size == 0:
            raise RuntimeError("No points parsed from ASCII PLY.")
        return pts

def umeyama(X, Y, with_scale=True):
    """
    Estimate s, R, t s.t. Y ≈ s*R*X + t (X,Y are Nx3).
    Returns s, R (3x3), t (3,)
    """
    X = np.asarray(X, dtype=np.float64)
    Y = np.asarray(Y, dtype=np.float64)
    assert X.shape == Y.shape and X.shape[1] == 3
    n = X.shape[0]
    mu_X = X.mean(axis=0)
    mu_Y = Y.mean(axis=0)
    Xc = X - mu_X
    Yc = Y - mu_Y
    # Covariance as in Umeyama: YX^T / n
    C = (Yc.T @ Xc) / n
    U, D, Vt = np.linalg.svd(C)
    S = np.eye(3)
    if np.linalg.det(U @ Vt) < 0:
        S[-1, -1] = -1.0
    R = U @ S @ Vt
    var_X = (Xc ** 2).sum() / n
    if with_scale:
        s = (D * np.diag(S)).sum() / var_X
    else:
        s = 1.0
    t = mu_Y - s * (R @ mu_X)
    return s, R, t

def transform_points(X, s, R, t):
    return (s * (R @ X.T)).T + t

def ransac_similarity(X, Y, with_scale=True, thresh=0.2, max_iters=10000, seed=0):
    """
    RANSAC for similarity (or rigid if with_scale=False).
    X -> Y
    thresh in same units as points (meters).
    """
    rng = np.random.default_rng(seed)
    n = X.shape[0]
    if n < 3:
        raise ValueError("Need at least 3 correspondences.")
    best_inliers = None
    best_model = None

    indices = np.arange(n)
    for _ in range(max_iters):
        # Sample 3 unique indices
        sample = rng.choice(indices, size=3, replace=False)
        try:
            s, R, t = umeyama(X[sample], Y[sample], with_scale=with_scale)
        except np.linalg.LinAlgError:
            continue
        # Score consensus
        pred = transform_points(X, s, R, t)
        residuals = np.linalg.norm(pred - Y, axis=1)
        inliers = residuals <= thresh
        score = inliers.sum()
        if best_inliers is None or score > best_inliers.sum():
            best_inliers = inliers
            best_model = (s, R, t)

    if best_inliers is None:
        raise RuntimeError("RANSAC failed to find a model.")

    # Refine on inliers
    s, R, t = umeyama(X[best_inliers], Y[best_inliers], with_scale=with_scale)
    pred = transform_points(X, s, R, t)
    residuals = np.linalg.norm(pred - Y, axis=1)
    inliers = residuals <= thresh
    rmse = np.sqrt((residuals[inliers] ** 2).mean()) if inliers.any() else float("nan")

    return (s, R, t), inliers, rmse

def save_matrix_txt(path, s, R, t):
    T = np.eye(4)
    T[:3, :3] = s * R
    T[:3, 3] = t
    np.savetxt(path, T, fmt="%.9f")
    return T

def maybe_save_aligned_ply(path, pts):
    try:
        import open3d as o3d
        pcd = o3d.geometry.PointCloud(o3d.utility.Vector3dVector(pts))
        o3d.io.write_point_cloud(path, pcd, write_ascii=True)
    except Exception:
        pass  # silently skip if Open3D not available

def main():
    ap = argparse.ArgumentParser(description="Robustly align VI and COLMAP camera centers with a (scaled) rigid transform.")
    ap.add_argument("ply_vi", help="PLY of visual-inertial camera centers (N points).")
    ap.add_argument("ply_colmap", help="PLY of COLMAP camera centers (N points).")
    ap.add_argument("--no-scale", action="store_true", help="Force pure rigid (R,t) without scale.")
    ap.add_argument("--thresh", type=float, default=0.20, help="RANSAC inlier threshold (meters). Default: 0.20")
    ap.add_argument("--iters", type=int, default=10000, help="RANSAC iterations. Default: 10000")
    ap.add_argument("--seed", type=int, default=0, help="Random seed.")
    ap.add_argument("--out-matrix", default="T_vi_to_colmap.txt", help="Where to save 4x4 transform.")
    ap.add_argument("--out-aligned", default=None, help="Optional PLY path to save VI points transformed into COLMAP frame.")
    args = ap.parse_args()

    X = load_points_from_ply(args.ply_vi)
    Y = load_points_from_ply(args.ply_colmap)
    if X.shape != Y.shape or X.shape[1] != 3:
        raise SystemExit(f"Point sets must both be Nx3 and same N. Got {X.shape} vs {Y.shape}.")

    with_scale = not args.no_scale

    (s, R, t), inliers, rmse = ransac_similarity(
        X, Y, with_scale=with_scale, thresh=args.thresh, max_iters=args.iters, seed=args.seed
    )
    T = save_matrix_txt(args.out_matrix, s, R, t)

    print("# Transform VI -> COLMAP (4x4):")
    np.set_printoptions(precision=6, suppress=True)
    print(T)
    print(f"\nScale: {s:.6f}  (set --no-scale to force s=1)")
    print(f"Inliers: {inliers.sum()}/{len(inliers)}  ({100*inliers.mean():.1f}%)")
    print(f"Inlier RMSE: {rmse:.4f}")

    if args.out_aligned:
        X_aligned = transform_points(X, s, R, t)
        maybe_save_aligned_ply(args.out_aligned, X_aligned)
        print(f"Wrote aligned VI points to: {args.out_aligned}")
    print(f"Saved matrix to: {args.out_matrix}")

if __name__ == "__main__":
    main()

'''
python align_camera_centers.py /home/luke/pamir/Combined_exhaustive/matched/svin_0.ply /home/luke/pamir/matchmania/Combined/seq_0.ply --thresh 0.20 --iters 20000 --out-matrix /home/luke/pamir/matchmania/Combined/T.txt --out-aligned /home/luke/pamir/matchmania/Combined/vi_in_colmap.ply
'''
