#!/usr/bin/env python3
"""
Rigidly align two nearly-aligned point clouds with Open3D (ICP).
Usage:
  python align_icp.py target.ply source.ply [--threshold 0.0] [--voxel 0.0] [--max-iter 50] [--method p2plane|p2point]

- The second file (source) will be transformed to match the first (target).
- Prints the 4x4 transform, rotation R, and translation t.
- Writes an aligned source file alongside the inputs.
"""
import argparse
from pathlib import Path
import numpy as np
import open3d as o3d

def auto_threshold(pcd):
    # Use 1% of the target's bounding-box diagonal as a sensible default
    bounds = pcd.get_max_bound() - pcd.get_min_bound()
    diag = np.linalg.norm(bounds)
    return max(1e-6, 0.01 * diag)

def estimate_normals(pcd, radius):
    pcd.estimate_normals(
        search_param=o3d.geometry.KDTreeSearchParamHybrid(radius=radius, max_nn=30)
    )
    return pcd

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("target", type=Path, help="Reference PLY (fixed)")
    ap.add_argument("source", type=Path, help="Moving PLY (will be aligned to target)")
    ap.add_argument("--threshold", type=float, default=0.0,
                    help="Max correspondence distance (same units as data). If 0, auto-compute (~1%% of target size).")
    ap.add_argument("--voxel", type=float, default=0.0,
                    help="Optional voxel size for downsampling before ICP (0 = no downsampling).")
    ap.add_argument("--max-iter", type=int, default=5000, help="ICP max iterations")
    ap.add_argument("--method", choices=["p2plane", "p2point"], default="p2point",
                    help="ICP estimation method (default: point-to-plane)")
    args = ap.parse_args()

    # Load
    tgt = o3d.io.read_point_cloud(str(args.target))
    src = o3d.io.read_point_cloud(str(args.source))
    if tgt.is_empty() or src.is_empty():
        raise SystemExit("One of the point clouds is empty or failed to load.")

    # Optional downsampling for speed/stability
    src_work = src
    tgt_work = tgt
    if args.voxel and args.voxel > 0:
        src_work = src.voxel_down_sample(args.voxel)
        tgt_work = tgt.voxel_down_sample(args.voxel)

    # Determine thresholds
    thresh = args.threshold if args.threshold > 0 else auto_threshold(tgt_work)
    normal_radius = max(thresh * 2.0, 1e-6)

    # Normals (required for point-to-plane; harmless for point-to-point)
    estimate_normals(tgt_work, normal_radius)
    estimate_normals(src_work, normal_radius)

    # ICP setup
    if args.method == "p2plane":
        estimation = o3d.pipelines.registration.TransformationEstimationPointToPlane()
    else:
        estimation = o3d.pipelines.registration.TransformationEstimationPointToPoint()

    criteria = o3d.pipelines.registration.ICPConvergenceCriteria(max_iteration=args.max_iter)

    # Initial guess = identity (they're nearly aligned)
    init = np.eye(4)

    # Run ICP on working (optionally downsampled) clouds
    reg = o3d.pipelines.registration.registration_icp(
        src_work, tgt_work, thresh, init, estimation, criteria
    )

    T = reg.transformation
    R, t = T[:3, :3], T[:3, 3]

    # Apply transform to the full-resolution source and save
    src_aligned = src.transform(T.copy())
    out_path = args.source.with_name(f"{args.source.stem}_aligned_to_{args.target.stem}.ply")
    o3d.io.write_point_cloud(str(out_path), src_aligned)

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
    print(f"\nAligned source saved to: {out_path}")

if __name__ == "__main__":
    main()
'''
python align_icp.py \
/mnt/Data2/luke/pamir/reconstructions/oneframe/Filtered/non_incref_point_clouds/pamir0.ply \
/mnt/Data2/luke/pamir/reconstructions/oneframe/Filtered/non_incref_point_clouds/pamir1.ply
'''

'''
python align_icp.py \
/mnt/Data2/luke/pamir/reconstructions/oneframe/Filtered/non_incref_point_clouds/pamir0.ply \
/mnt/Data2/luke/pamir/reconstructions/oneframe/Filtered/non_incref_point_clouds/pamir0_transformed.ply
'''

'''
python align_icp.py \
/mnt/Data3/luke/underwater/Results/Pamir1/partial_detection/transformation_only_with_4x2/pointCloud_Pamir1_partial_det_transform_only_with_4x2.ply \
/mnt/Data3/luke/underwater/Results/Pamir2/partial_detection/transformation_only_with_4x2/pointCloud_Pamir2trim_partial_det_transform_only_with_4x2.ply
'''