#!/usr/bin/env python3
"""
Fast point cloud alignment with Open3D:
- Global registration via RANSAC on FPFH features
- Local refinement via ICP (point-to-plane) on the DOWNSAMPLED clouds by default (for speed)
- Optionally refine on full resolution with --full-icp

Usage:
  python align_point_clouds.py <target.ply/pcd/...> <source.ply/pcd/...> \
      [--voxel-size 0.02] [--out-transform transform.npy] [--out-pcd aligned_source.ply] \
      [--preview] [--full-icp] [--max-iters-ransac 100000] [--max-iters-icp 30] [--quiet]

Notes:
- Prioritizes SPEED. For higher accuracy, reduce voxel size, increase RANSAC/ICP iters, and enable --full-icp.
- Assumes source should be aligned INTO the target’s frame.
"""

import argparse
import logging
import sys
from pathlib import Path
import numpy as np

try:
    import open3d as o3d
except Exception as e:
    print("This script requires Open3D. Install with: pip install open3d", file=sys.stderr)
    raise

# -------------------------
# Utilities
# -------------------------

def setup_logging(quiet: bool):
    level = logging.WARNING if quiet else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s | %(levelname)s | %(message)s",
        datefmt="%H:%M:%S",
    )

def read_point_cloud(path: Path) -> o3d.geometry.PointCloud:
    logging.info(f"Reading point cloud: {path}")
    pcd = o3d.io.read_point_cloud(str(path))
    if pcd.is_empty():
        raise ValueError(f"Loaded empty point cloud from {path}")
    logging.info(f"Loaded {path.name}: {np.asarray(pcd.points).shape[0]:,} points")
    return pcd

def guess_voxel_size_from_scale(pcd: o3d.geometry.PointCloud) -> float:
    # Heuristic: 2% of bbox diagonal (clamped), speed-oriented
    aabb = pcd.get_axis_aligned_bounding_box()
    diag = np.linalg.norm(aabb.get_max_bound() - aabb.get_min_bound())
    vs = max(0.0025, min(0.1, 0.02 * float(diag)))
    logging.info(f"Guessed voxel size from scale: {vs:.5f}")
    return vs

def remove_outliers_fast(pcd: o3d.geometry.PointCloud, nb_neighbors=16, std_ratio=1.5):
    logging.info("Optional: quick statistical outlier removal (fast settings)")
    pcd_denoised, idx = pcd.remove_statistical_outlier(nb_neighbors=nb_neighbors, std_ratio=std_ratio)
    logging.info(f"  Kept {np.asarray(pcd_denoised.points).shape[0]:,} / {np.asarray(pcd.points).shape[0]:,} points")
    return pcd_denoised

def preprocess(pcd: o3d.geometry.PointCloud, voxel_size: float, estimate_normals_on_down=True):
    logging.info(f"Preprocess: voxel downsample at {voxel_size:.5f}")
    pcd_down = pcd.voxel_down_sample(voxel_size)
    logging.info(f"  Downsampled to {np.asarray(pcd_down.points).shape[0]:,} points")

    # Normals on downsampled cloud (needed for FPFH, and for point-to-plane ICP if used later)
    if estimate_normals_on_down:
        r_normal = 2.0 * voxel_size
        logging.info(f"  Estimating normals (radius={r_normal:.5f}, max_nn=20)")
        pcd_down.estimate_normals(
            o3d.geometry.KDTreeSearchParamHybrid(radius=r_normal, max_nn=20)
        )
        pcd_down.orient_normals_consistent_tangent_plane(10)

    # FPFH features
    r_fpfh = 5.0 * voxel_size
    logging.info(f"  Computing FPFH (radius={r_fpfh:.5f}, max_nn=64)")
    fpfh = o3d.pipelines.registration.compute_fpfh_feature(
        pcd_down,
        o3d.geometry.KDTreeSearchParamHybrid(radius=r_fpfh, max_nn=64)
    )
    return pcd_down, fpfh

def ensure_normals(pcd: o3d.geometry.PointCloud, voxel_size: float):
    # For speed, compute normals with a modest radius on-demand
    if not pcd.has_normals():
        r_normal = 2.0 * voxel_size
        logging.info(f"Estimating normals on full-res (radius={r_normal:.5f}, max_nn=30)")
        pcd.estimate_normals(
            o3d.geometry.KDTreeSearchParamHybrid(radius=r_normal, max_nn=30)
        )
        pcd.orient_normals_consistent_tangent_plane(20)

def global_registration_ransac(source_down, target_down, fpfh_s, fpfh_t, voxel_size, max_iters_ransac):
    distance_threshold = 1.5 * voxel_size
    logging.info(f"Global registration (RANSAC): "
                 f"dist_thresh={distance_threshold:.5f}, ransac_n=4, max_iters={max_iters_ransac}")

    checkers = [
        o3d.pipelines.registration.CorrespondenceCheckerBasedOnEdgeLength(0.9),
        o3d.pipelines.registration.CorrespondenceCheckerBasedOnDistance(distance_threshold),
    ]
    result = o3d.pipelines.registration.registration_ransac_based_on_feature_matching(
        source_down, target_down, fpfh_s, fpfh_t,
        True,  # mutual filter
        distance_threshold,
        o3d.pipelines.registration.TransformationEstimationPointToPoint(False),
        4,  # ransac_n
        checkers,
        # (max_iteration, max_validation) — speed-oriented values:
        o3d.pipelines.registration.RANSACConvergenceCriteria(max_iters_ransac, 1000),
    )
    logging.info("RANSAC done.")
    logging.info(f"  RANSAC fitness: {result.fitness:.4f}")
    logging.info(f"  RANSAC inlier_rmse: {result.inlier_rmse:.6f}")
    logging.info(f"  RANSAC transform:\n{result.transformation}")
    return result

def icp_refine(source, target, init_T, voxel_size, max_iters_icp, full_res=False):
    # For speed, use a single-stage point-to-plane ICP with a modest correspondence threshold
    # If running on downsampled clouds, this is fast; full-res is optional and slower.
    max_corr_dist = 0.5 * voxel_size
    logging.info(f"ICP ({'full-res' if full_res else 'downsampled'}): "
                 f"max_corr_dist={max_corr_dist:.5f}, max_iters={max_iters_icp}")
    estimation = o3d.pipelines.registration.TransformationEstimationPointToPlane()
    criteria = o3d.pipelines.registration.ICPConvergenceCriteria(max_iteration=max_iters_icp)

    result = o3d.pipelines.registration.registration_icp(
        source, target,
        max_correspondence_distance=max_corr_dist,
        init=init_T,
        estimation_method=estimation,
        criteria=criteria,
    )
    logging.info("ICP done.")
    logging.info(f"  ICP fitness: {result.fitness:.4f}")
    logging.info(f"  ICP inlier_rmse: {result.inlier_rmse:.6f}")
    logging.info(f"  ICP transform:\n{result.transformation}")
    return result

def colorize_for_preview(pcd, color):
    pcdc = o3d.geometry.PointCloud(pcd)
    pcdc.paint_uniform_color(color)
    return pcdc

# -------------------------
# Main
# -------------------------

def main():
    parser = argparse.ArgumentParser(description="Fast RANSAC+ICP point cloud alignment (Open3D).")
    parser.add_argument("target", type=Path, help="Target point cloud (reference frame).")
    parser.add_argument("source", type=Path, help="Source point cloud (to be aligned into target).")

    parser.add_argument("--voxel-size", type=float, default=None,
                        help="Downsample size (meters). If omitted, guessed from target scale (speed-oriented).")
    parser.add_argument("--full-icp", action="store_true",
                        help="Also run ICP on FULL resolution (slower, more accurate).")
    parser.add_argument("--max-iters-ransac", type=int, default=100000,
                        help="Max RANSAC iterations (speed default: 100000).")
    parser.add_argument("--max-iters-icp", type=int, default=30,
                        help="Max ICP iterations (speed default: 30).")
    parser.add_argument("--out-transform", type=Path, default=None,
                        help="Path to save final 4x4 transform as .npy")
    parser.add_argument("--out-pcd", type=Path, default=None,
                        help="Path to save the source transformed into target frame (e.g., aligned_source.ply)")
    parser.add_argument("--preview", action="store_true",
                        help="Show an Open3D preview window with overlaid clouds.")
    parser.add_argument("--denoise", action="store_true",
                        help="Apply fast statistical outlier removal before processing.")
    parser.add_argument("--quiet", action="store_true",
                        help="Reduce logging verbosity.")

    args = parser.parse_args()
    setup_logging(args.quiet)

    # Load
    target = read_point_cloud(args.target)
    source = read_point_cloud(args.source)

    if args.denoise:
        target = remove_outliers_fast(target)
        source = remove_outliers_fast(source)

    # Voxel size heuristic (speed-first)
    voxel_size = args.voxel_size if args.voxel_size and args.voxel_size > 0 else guess_voxel_size_from_scale(target)
    logging.info(f"Using voxel_size={voxel_size:.5f}")

    # Preprocess for global registration
    target_down, target_fpfh = preprocess(target, voxel_size)
    source_down, source_fpfh = preprocess(source, voxel_size)

    # Global alignment (RANSAC on FPFH)
    ransac = global_registration_ransac(
        source_down, target_down, source_fpfh, target_fpfh, voxel_size, args.max_iters_ransac
    )

    # ICP refinement on **downsampled** (fast)
    icp_down = icp_refine(
        source_down, target_down, ransac.transformation, voxel_size, args.max_iters_icp, full_res=False
    )
    T = icp_down.transformation

    # Optional full-res ICP for better accuracy
    if args.full_icp:
        # Ensure normals (point-to-plane)
        ensure_normals(target, voxel_size)
        ensure_normals(source, voxel_size)
        # Transform a copy of the source for refinement
        source_init = o3d.geometry.PointCloud(source)
        source_init.transform(T)
        icp_full = icp_refine(
            source_init, target, np.eye(4), voxel_size, max_iters_icp=args.max_iters_icp, full_res=True
        )
        T = icp_full.transformation @ T  # compose

    logging.info("Final transform (source -> target):")
    logging.info("\n" + str(T))

    # Save outputs
    if args.out_transform:
        np.save(args.out_transform, T)
        logging.info(f"Saved transform to {args.out_transform}")

    if args.out_pcd:
        aligned = o3d.geometry.PointCloud(source)
        aligned.transform(T)
        ok = o3d.io.write_point_cloud(str(args.out_pcd), aligned, write_ascii=False, compressed=True)
        if ok:
            logging.info(f"Saved aligned source to {args.out_pcd}")
        else:
            logging.warning(f"Failed to save aligned source to {args.out_pcd}")

    # Preview
    if args.preview:
        aligned_vis = o3d.geometry.PointCloud(source)
        aligned_vis.transform(T)
        tgt_c = colorize_for_preview(target, [0.0, 0.651, 0.929])     # blue-ish
        src_c = colorize_for_preview(aligned_vis, [1.0, 0.706, 0.0])  # orange-ish
        logging.info("Opening interactive preview window… (close it to finish)")
        o3d.visualization.draw_geometries([tgt_c, src_c])

    logging.info("Done.")

if __name__ == "__main__":
    main()

'''
python align_point_clouds.py \
    /mnt/Data2/luke/pamir/reconstructions/oneframe/Filtered/incref_pc/pamir0.ply \
    /mnt/Data2/luke/pamir/reconstructions/oneframe/Filtered/incref_pc/pamir1.ply \
    --out-pcd /mnt/Data2/luke/pamir/reconstructions/oneframe/Filtered/incref_pc/pamir1_aligned_to_pamir0.ply \
    --voxel-size 0.1 \
    --max-iters-ransac 1000000 \
    --max-iters-icp 80 \
    --full-icp --preview
'''