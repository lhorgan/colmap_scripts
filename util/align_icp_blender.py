#!/usr/bin/env python3
"""
Rigidly align two nearly-aligned point clouds with Open3D (ICP), now with an optional
initial transform from Blender (Euler+translation) or a full 4x4 matrix.

Usage:
  python align_icp.py target.ply source.ply
  [--threshold 0.0] [--voxel 0.0] [--max-iter 50] [--method p2plane|p2point]
  # Initial guess (choose ONE approach):

  # (A) Direct relative pose (source -> target):
  --init-translation tx ty tz --init-euler rx ry rz --euler-order XYZ

  # (B) Two world poses (from Blender):
  --tgt-translation Tx Ty Tz --tgt-euler Rx Ry Rz
  --src-translation Sx Sy Sz --src-euler Rx Ry Rz
  --euler-order XYZ

  # (C) 4x4 matrix file (source -> target):
  --init-matrix path/to/matrix.txt

Matrix file may be whitespace 4x4 or JSON [[...],[...],[...],[...]].

Examples:
  # Single relative pose:
  python align_icp.py tgt.ply src.ply --init-translation 0.01 0.0 -0.02 --init-euler 0 0 5 --euler-order XYZ

  # Two Blender world poses (rotation mode XYZ):
  python align_icp.py tgt.ply src.ply \
    --tgt-translation 0.0 0.0 0.0 --tgt-euler 0 0 0 \
    --src-translation 0.12 -0.03 0.01 --src-euler 0 5 0 \
    --euler-order XYZ

  # Direct 4x4:
  python align_icp.py tgt.ply src.ply --init-matrix T_init.txt
"""
import argparse
from pathlib import Path
import numpy as np
import open3d as o3d
import json

def auto_threshold(pcd):
    bounds = pcd.get_max_bound() - pcd.get_min_bound()
    diag = np.linalg.norm(bounds)
    return max(1e-6, 0.01 * diag)

def rot_x(a): c,s=np.cos(a),np.sin(a); return np.array([[1,0,0],[0,c,-s],[0,s,c]])
def rot_y(a): c,s=np.cos(a),np.sin(a); return np.array([[c,0,s],[0,1,0],[-s,0,c]])
def rot_z(a): c,s=np.cos(a),np.sin(a); return np.array([[c,-s,0],[s,c,0],[0,0,1]])

_AXIS_FUN = {'X': rot_x, 'Y': rot_y, 'Z': rot_z}

def euler_intrinsic_deg_to_R(rx_deg, ry_deg, rz_deg, order="XYZ"):
    """
    Blender-like intrinsic Euler. For order 'XYZ', matrix = Rz * Ry * Rx (note reversal in product).
    Angles are in degrees, applied about the CURRENT local axes in given order.
    """
    angles_rad = {'X': np.deg2rad(rx_deg), 'Y': np.deg2rad(ry_deg), 'Z': np.deg2rad(rz_deg)}
    # Build in intrinsic sense: R = R_axis_last * ... * R_axis_first
    R = np.eye(3)
    for ax in reversed(order.upper()):
        R = _AXIS_FUN[ax](angles_rad[ax]) @ R
    return R

def make_T(R, t):
    T = np.eye(4)
    T[:3,:3] = R
    T[:3, 3] = np.asarray(t, dtype=float)
    return T

def parse_vec3(vals, name):
    if vals is None or len(vals)!=3:
        raise ValueError(f"{name} must have three numbers.")
    return np.array(list(map(float, vals)), dtype=float)

def read_matrix4x4(path):
    txt = Path(path).read_text().strip()
    try:
        arr = np.array(json.loads(txt), dtype=float)
    except Exception:
        # Fallback: whitespace matrix
        rows = [list(map(float, line.split())) for line in txt.splitlines() if line.strip()]
        arr = np.array(rows, dtype=float)
    if arr.shape != (4,4):
        raise ValueError(f"Matrix in {path} must be 4x4, got {arr.shape}.")
    return arr

def build_init_from_args(args):
    # Priority: matrix file > two poses > single relative pose > identity
    if args.init_matrix:
        T = read_matrix4x4(args.init_matrix)
        return T, "matrix-file"

    if args.tgt_translation and args.tgt_euler and args.src_translation and args.src_euler:
        tT = parse_vec3(args.tgt_translation, "tgt-translation")
        rT = parse_vec3(args.tgt_euler,       "tgt-euler (deg)")
        tS = parse_vec3(args.src_translation, "src-translation")
        rS = parse_vec3(args.src_euler,       "src-euler (deg)")
        R_T = euler_intrinsic_deg_to_R(rT[0], rT[1], rT[2], args.euler_order)
        R_S = euler_intrinsic_deg_to_R(rS[0], rS[1], rS[2], args.euler_order)
        T_T = make_T(R_T, tT)
        T_S = make_T(R_S, tS)
        T = T_T @ np.linalg.inv(T_S)   # world_tgt * inv(world_src) : source -> target
        return T, "two-poses"

    if args.init_translation or args.init_euler:
        if not (args.init_translation and args.init_euler):
            raise ValueError("Provide BOTH --init-translation and --init-euler for a relative pose.")
        t = parse_vec3(args.init_translation, "init-translation")
        r = parse_vec3(args.init_euler,       "init-euler (deg)")
        R = euler_intrinsic_deg_to_R(r[0], r[1], r[2], args.euler_order)
        T = make_T(R, t)
        return T, "relative"

    return np.eye(4), "identity"

def estimate_normals(pcd, radius):
    pcd.estimate_normals(
        search_param=o3d.geometry.KDTreeSearchParamHybrid(radius=radius, max_nn=30)
    )
    return pcd

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("target", type=Path, help="Reference PLY (fixed)")
    ap.add_argument("source", type=Path, help="Moving PLY (will be aligned to target)")

    # ICP controls
    ap.add_argument("--threshold", type=float, default=0.0,
                    help="Max correspondence distance. If 0, auto (~1%% of target size).")
    ap.add_argument("--voxel", type=float, default=0.0,
                    help="Optional voxel size (0 = no downsampling).")
    ap.add_argument("--max-iter", type=int, default=50, help="ICP max iterations")
    ap.add_argument("--method", choices=["p2plane", "p2point"], default="p2plane",
                    help="ICP estimation method")

    # Initial transform inputs
    ap.add_argument("--init-matrix", type=str, default=None,
                    help="Path to 4x4 matrix (JSON or whitespace) for source->target.")
    ap.add_argument("--init-translation", nargs=3, type=float, default=None,
                    help="Relative translation tx ty tz (source->target).")
    ap.add_argument("--init-euler", nargs=3, type=float, default=None,
                    help="Relative Euler angles rx ry rz in degrees (source->target).")
    ap.add_argument("--euler-order", type=str, default="XYZ",
                    help="Euler rotation order (matches Blender rotation mode, e.g., XYZ, ZXY, etc.)")

    # Two world poses (Blender) for target and source
    ap.add_argument("--tgt-translation", nargs=3, type=float, default=None,
                    help="Target world translation Tx Ty Tz (from Blender).")
    ap.add_argument("--tgt-euler", nargs=3, type=float, default=None,
                    help="Target world Euler Rx Ry Rz in degrees (from Blender).")
    ap.add_argument("--src-translation", nargs=3, type=float, default=None,
                    help="Source world translation Sx Sy Sz (from Blender).")
    ap.add_argument("--src-euler", nargs=3, type=float, default=None,
                    help="Source world Euler Rx Ry Rz in degrees (from Blender).")

    args = ap.parse_args()

    # Load
    tgt = o3d.io.read_point_cloud(str(args.target))
    src = o3d.io.read_point_cloud(str(args.source))
    if tgt.is_empty() or src.is_empty():
        raise SystemExit("One of the point clouds is empty or failed to load.")

    # Optional downsampling for speed/stability
    src_work, tgt_work = src, tgt
    if args.voxel and args.voxel > 0:
        src_work = src.voxel_down_sample(args.voxel)
        tgt_work = tgt.voxel_down_sample(args.voxel)

    # Threshold & normals
    thresh = args.threshold if args.threshold > 0 else auto_threshold(tgt_work)
    normal_radius = max(thresh * 2.0, 1e-6)
    estimate_normals(tgt_work, normal_radius)
    estimate_normals(src_work, normal_radius)

    # Initial guess
    T_init, init_mode = build_init_from_args(args)

    # ICP setup
    if args.method == "p2plane":
        estimation = o3d.pipelines.registration.TransformationEstimationPointToPlane()
    else:
        estimation = o3d.pipelines.registration.TransformationEstimationPointToPoint()

    criteria = o3d.pipelines.registration.ICPConvergenceCriteria(max_iteration=args.max_iter)

    print("\n=== Initial Guess (source → target) [{}] ===".format(init_mode))
    np.set_printoptions(precision=6, suppress=True)
    print(T_init)

    # Run ICP
    reg = o3d.pipelines.registration.registration_icp(
        src_work, tgt_work, thresh, T_init, estimation, criteria
    )
    T = reg.transformation
    R, t = T[:3,:3], T[:3,3]

    # Apply to full-res source and save
    src_aligned = src.transform(T.copy())
    out_path = args.source.with_name(f"{args.source.stem}_aligned_to_{args.target.stem}.ply")
    o3d.io.write_point_cloud(str(out_path), src_aligned)

    # Report
    print("\n=== ICP Result ===")
    print(f"Fitness (inlier ratio): {reg.fitness:.6f}")
    print(f"RMSE: {reg.inlier_rmse:.6f}")
    print(f"Correspondence threshold: {thresh:.6f}")
    print("\nFinal transformation (source → target), 4x4:\n", T)
    print("\nR (3x3):\n", R)
    print("\nt (xyz):", t)
    print(f"\nAligned source saved to: {out_path}")

if __name__ == "__main__":
    main()

'''
python align_icp_blender.py /mnt/Data2/luke/pamir/reconstructions/oneframe/Filtered/incref_pc/pamir0.ply /mnt/Data2/luke/pamir/reconstructions/oneframe/Filtered/incref_pc/pamir1.ply --init-translation -4.3163 -1.2134 0 --init-euler 0 0 -2.2 --euler-order XYZ
'''

'''
python align_icp_blender.py /mnt/Data2/luke/pamir/reconstructions/oneframe/Filtered/incref_pc/pamir1.ply /mnt/Data2/luke/pamir/reconstructions/oneframe/Filtered/incref_pc/pamir2.ply --init-translation 3.1679 1.45 -0.49289 --init-euler 0 0 0.352 --euler-order XYZ
'''
