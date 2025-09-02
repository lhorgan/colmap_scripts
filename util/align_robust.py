#!/usr/bin/env python3
"""
Robust point-cloud alignment with Open3D:
- Optional global init (RANSAC or FGR) using FPFH features
- Multi-scale ICP refine (tightening thresholds)
- Tight scoring to ensure strong overlap
- Optional manual/Blender initial transform as a candidate

Usage:
  python align_robust.py target.ply source.ply
    [--global-init auto|fgr|ransac|none]
    [--method p2plane|p2point]
    [--voxel -1]               # feature voxel; -1 => auto (1% of diag)
    [--icp-levels 3]           # num multiscale levels (3 recommended)
    [--iters 150]              # ICP iters per level
    [--seed 0]                 # for RANSAC reproducibility
    [--save src_aligned.ply]

  # Optionally provide a manual/Blender init as an alternative candidate:
  --init-matrix T.txt
  --init-translation tx ty tz --init-euler rx ry rz --euler-order XYZ
  --tgt-translation Tx Ty Tz --tgt-euler Rx Ry Rz
  --src-translation Sx Sy Sz --src-euler Rx Ry Rz

The script will try the requested global init (or 'auto'), optionally also
your manual init, refine both with ICP, then choose the one with the best
tight-radius fitness (breaking ties by lower RMSE).
"""
from pathlib import Path
import argparse, json, copy
import numpy as np
import open3d as o3d

# ---------- Utilities ----------
def bbox_diag(pcd):
    return float(np.linalg.norm(pcd.get_max_bound() - pcd.get_min_bound()))

def voxel_down(pcd, v):
    return pcd if v <= 0 else pcd.voxel_down_sample(v)

def estimate_normals(pcd, radius, max_nn=30):
    pcd.estimate_normals(o3d.geometry.KDTreeSearchParamHybrid(radius=radius, max_nn=max_nn))
    return pcd

def compute_fpfh(pcd, radius):
    return o3d.pipelines.registration.compute_fpfh_feature(
        pcd, o3d.geometry.KDTreeSearchParamHybrid(radius=radius, max_nn=100)
    )

def rot_x(a): c,s=np.cos(a),np.sin(a); return np.array([[1,0,0],[0,c,-s],[0,s,c]])
def rot_y(a): c,s=np.cos(a),np.sin(a); return np.array([[c,0,s],[0,1,0],[-s,0,c]])
def rot_z(a): c,s=np.cos(a),np.sin(a); return np.array([[c,-s,0],[s,c,0],[0,0,1]])
_AXIS_FUN = {'X': rot_x, 'Y': rot_y, 'Z': rot_z}

def euler_intrinsic_deg_to_R(rx_deg, ry_deg, rz_deg, order="XYZ"):
    # Blender-like intrinsic Euler: for order 'XYZ' => R = Rz * Ry * Rx
    angles = {'X': np.deg2rad(rx_deg), 'Y': np.deg2rad(ry_deg), 'Z': np.deg2rad(rz_deg)}
    R = np.eye(3)
    for ax in reversed(order.upper()):
        R = _AXIS_FUN[ax](angles[ax]) @ R
    return R

def make_T(R, t):
    T = np.eye(4); T[:3,:3] = R; T[:3,3] = np.asarray(t, float); return T

def parse_vec3(vals, name):
    if vals is None or len(vals)!=3: raise ValueError(f"{name} must have 3 numbers")
    return np.array(list(map(float, vals)), float)

def read_matrix4x4(path):
    txt = Path(path).read_text().strip()
    try:
        arr = np.array(json.loads(txt), float)
    except Exception:
        rows = [list(map(float, ln.split())) for ln in txt.splitlines() if ln.strip()]
        arr = np.array(rows, float)
    if arr.shape != (4,4): raise ValueError(f"Matrix in {path} must be 4x4, got {arr.shape}")
    return arr

def build_manual_init(args):
    # Priority: matrix > two world poses > relative pose > None
    if args.init_matrix:
        return read_matrix4x4(args.init_matrix), "manual-matrix"
    if args.tgt_translation and args.tgt_euler and args.src_translation and args.src_euler:
        tT = parse_vec3(args.tgt_translation, "tgt-translation")
        rT = parse_vec3(args.tgt_euler, "tgt-euler (deg)")
        tS = parse_vec3(args.src_translation, "src-translation")
        rS = parse_vec3(args.src_euler, "src-euler (deg)")
        R_T = euler_intrinsic_deg_to_R(*rT, order=args.euler_order)
        R_S = euler_intrinsic_deg_to_R(*rS, order=args.euler_order)
        T = make_T(R_T, tT) @ np.linalg.inv(make_T(R_S, tS))
        return T, "manual-two-world-poses"
    if args.init_translation and args.init_euler:
        t = parse_vec3(args.init_translation, "init-translation")
        r = parse_vec3(args.init_euler, "init-euler (deg)")
        T = make_T(euler_intrinsic_deg_to_R(*r, order=args.euler_order), t)
        return T, "manual-relative"
    return None, None

# ---------- Global initializers ----------
def global_init_fgr(src_d, tgt_d, f_src, f_tgt, dist):
    option = o3d.pipelines.registration.FastGlobalRegistrationOption(
        maximum_correspondence_distance=dist
    )
    reg = o3d.pipelines.registration.registration_fast_based_on_feature_matching(
        src_d, tgt_d, f_src, f_tgt, option
    )
    return reg.transformation, reg

def global_init_ransac(src_d, tgt_d, f_src, f_tgt, dist, ransac_n=4, max_iter=300000, confidence=0.999, seed=0):
    # Optional seed (if supported by your Open3D version)
    try:
        o3d.utility.random.seed(seed)
    except Exception:
        pass
    checkers = [
        o3d.pipelines.registration.CorrespondenceCheckerBasedOnEdgeLength(0.9),
        o3d.pipelines.registration.CorrespondenceCheckerBasedOnDistance(dist),
    ]
    reg = o3d.pipelines.registration.registration_ransac_based_on_feature_matching(
        src_d, tgt_d, f_src, f_tgt, mutual_filter=True,
        max_correspondence_distance=dist,
        estimation_method=o3d.pipelines.registration.TransformationEstimationPointToPoint(False),
        ransac_n=ransac_n,
        checkers=checkers,
        criteria=o3d.pipelines.registration.RANSACConvergenceCriteria(max_iter, confidence),
    )
    return reg.transformation, reg

# ---------- ICP (multi-scale) ----------
def make_estimation(method="p2plane", robust=False, loss="tukey", k=1.0):
    # Robust kernels API varies slightly across Open3D versions; try gracefully.
    if method == "p2point":
        if robust:
            try:
                rk = o3d.pipelines.registration.RobustKernel(
                    getattr(o3d.pipelines.registration.RobustKernelType, "Tukey" if loss=="tukey" else "Huber"), k
                )
                return o3d.pipelines.registration.TransformationEstimationPointToPoint(False, rk)
            except Exception:
                pass
        return o3d.pipelines.registration.TransformationEstimationPointToPoint()
    else:
        if robust:
            try:
                rk = o3d.pipelines.registration.RobustKernel(
                    getattr(o3d.pipelines.registration.RobustKernelType, "Tukey" if loss=="tukey" else "Huber"), k
                )
                return o3d.pipelines.registration.TransformationEstimationPointToPlane(rk)
            except Exception:
                pass
        return o3d.pipelines.registration.TransformationEstimationPointToPlane()

def multiscale_icp(src, tgt, T0, method, levels, iters, v, robust=True):
    # thresholds shrink: [2.5v, 1.5v, 1.0v] (trim if fewer levels)
    base = [2.5*v, 1.5*v, 1.0*v]
    dists = base[:max(1, levels)]
    T = T0.copy()
    for i, dist in enumerate(dists):
        estimation = make_estimation(method=method, robust=robust, k=1.0*v)
        criteria = o3d.pipelines.registration.ICPConvergenceCriteria(max_iteration=int(iters))
        reg = o3d.pipelines.registration.registration_icp(src, tgt, dist, T, estimation, criteria)
        T = reg.transformation
    return T

# ---------- Scoring ----------
def tight_score(src, tgt, T, tight_dist):
    ev = o3d.pipelines.registration.evaluate_registration(src, tgt, tight_dist, T)
    return ev.fitness, ev.inlier_rmse

# ---------- Main ----------
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("target", type=Path)
    ap.add_argument("source", type=Path)

    ap.add_argument("--global-init", choices=["auto","fgr","ransac","none"], default="auto",
                    help="How to get an initial pose without manual input.")
    ap.add_argument("--method", choices=["p2plane","p2point"], default="p2plane",
                    help="ICP error model.")
    ap.add_argument("--voxel", type=float, default=-1.0,
                    help="Feature voxel size in data units; -1 => auto = 1%% of target bbox diag.")
    ap.add_argument("--icp-levels", type=int, default=3,
                    help="Number of ICP scales (tightening thresholds).")
    ap.add_argument("--iters", type=int, default=150,
                    help="ICP iterations per level.")
    ap.add_argument("--seed", type=int, default=0, help="RANSAC seed.")
    ap.add_argument("--save", type=Path, default=None, help="Output path for aligned source PLY.")

    # Manual / Blender init options (optional)
    ap.add_argument("--init-matrix", type=str, default=None)
    ap.add_argument("--init-translation", nargs=3, type=float, default=None)
    ap.add_argument("--init-euler", nargs=3, type=float, default=None)
    ap.add_argument("--euler-order", type=str, default="XYZ")
    ap.add_argument("--tgt-translation", nargs=3, type=float, default=None)
    ap.add_argument("--tgt-euler", nargs=3, type=float, default=None)
    ap.add_argument("--src-translation", nargs=3, type=float, default=None)
    ap.add_argument("--src-euler", nargs=3, type=float, default=None)

    args = ap.parse_args()

    # Load full-res clouds
    tgt_full = o3d.io.read_point_cloud(str(args.target))
    src_full = o3d.io.read_point_cloud(str(args.source))
    if tgt_full.is_empty() or src_full.is_empty():
        raise SystemExit("One of the point clouds failed to load or is empty.")

    diag = bbox_diag(tgt_full)
    if diag == 0.0:
        raise SystemExit("Target has zero bbox diagonal.")

    # Scale parameters
    v = (0.01 * diag) if args.voxel <= 0 else args.voxel
    v = max(v, 1e-9)  # guard
    r_norm = 2.0 * v
    r_feat = 5.0 * v
    d_global = 1.5 * v
    d_tight = 0.75 * v

    # Preprocess downsampled for features and (faster) ICP
    tgt_d = voxel_down(tgt_full, v); estimate_normals(tgt_d, r_norm)
    src_d = voxel_down(src_full, v); estimate_normals(src_d, r_norm)

    # Compute FPFH if we might need global init
    f_tgt = f_src = None
    if args.global_init in ("auto", "fgr", "ransac"):
        f_tgt = compute_fpfh(tgt_d, r_feat)
        f_src = compute_fpfh(src_d, r_feat)

    # Build candidate initial transforms
    candidates = []

    # Manual/Blender init (if provided)
    T_man, tag = build_manual_init(args)
    if T_man is not None:
        candidates.append(("manual", T_man))

    # Global init
    if args.global_init in ("fgr","auto"):
        T_fgr, reg = global_init_fgr(src_d, tgt_d, f_src, f_tgt, d_global)
        candidates.append(("fgr", T_fgr))
    if args.global_init in ("ransac","auto"):
        T_ransac, reg = global_init_ransac(src_d, tgt_d, f_src, f_tgt, d_global, seed=args.seed)
        candidates.append(("ransac", T_ransac))

    # If none requested, fall back to identity
    if not candidates and args.global_init == "none":
        candidates.append(("identity", np.eye(4)))

    if not candidates:
        # If user didn't ask for global init and gave no manual: still do identity
        candidates.append(("identity", np.eye(4)))

    # Refine each candidate with multi-scale ICP and pick the best by tight fitness, then RMSE
    results = []
    for name, T0 in candidates:
        T_ref = multiscale_icp(src_d, tgt_d, T0, args.method, args.icp_levels, args.iters, v, robust=True)
        fit, rmse = tight_score(src_d, tgt_d, T_ref, d_tight)
        results.append((fit, rmse, name, T_ref))

    results.sort(key=lambda x: (-x[0], x[1]))  # best = highest fitness, then lowest RMSE
    best_fit, best_rmse, best_name, T_best_down = results[0]

    # Optional final fine ICP on FULL resolution at the tightest distance
    estimation = make_estimation(method=args.method, robust=True, k=1.0*v)
    fine = o3d.pipelines.registration.registration_icp(
        src_full, tgt_full, 1.0*v, T_best_down,
        estimation,
        o3d.pipelines.registration.ICPConvergenceCriteria(max_iteration=int(args.iters))
    )
    T_final = fine.transformation
    fit_final, rmse_final = tight_score(src_full, tgt_full, T_final, d_tight)

    # Apply to full-res and save
    out_path = args.save if args.save else args.source.with_name(f"{args.source.stem}_aligned_to_{args.target.stem}.ply")
    src_aligned = copy.deepcopy(src_full)
    src_aligned.transform(T_final)
    o3d.io.write_point_cloud(str(out_path), src_aligned)

    # Report
    np.set_printoptions(precision=6, suppress=True)
    print("\n=== Parameters (auto-scaled) ===")
    print(f"diag(target)         : {diag:.6g}")
    print(f"voxel v              : {v:.6g}")
    print(f"normals radius       : {r_norm:.6g}")
    print(f"FPFH radius          : {r_feat:.6g}")
    print(f"global dist          : {d_global:.6g}")
    print(f"tight score dist     : {d_tight:.6g}")

    print("\n=== Candidate inits & tight scores (on downsampled) ===")
    for fit, rmse, name, T in results:
        print(f"- {name:9s} | fitness={fit:.4f} rmse={rmse:.6f}")

    print(f"\nChosen init: {best_name}")
    print("\n=== Final transform (source → target), 4×4 ===\n", T_final)
    print("\nRotation R (3×3):\n", T_final[:3,:3])
    print("\nTranslation t (xyz):", T_final[:3,3])
    print("\n=== Final tight score (full-res) ===")
    print(f"fitness={fit_final:.4f}  rmse={rmse_final:.6f}")
    print(f"\nAligned source saved to: {out_path}")

if __name__ == "__main__":
    main()

# https://chatgpt.com/c/68b1c421-51e8-832a-aa23-a7b12635ca3a

'''
python align_robust.py target.ply source.ply \
  --init-translation tx ty tz --init-euler rx ry rz --euler-order XYZ \
  --global-init auto
'''

# python align_robust.py /mnt/Data2/luke/pamir/reconstructions/oneframe/Filtered/incref_pc/pamir0.ply /mnt/Data2/luke/pamir/reconstructions/oneframe/Filtered/incref_pc/pamir1.ply --init-translation 4.3163 1.2134 0 --init-euler 0 0 2.2 --euler-order XYZ --global-init auto

# python align_robust.py /mnt/Data2/luke/pamir/reconstructions/oneframe/Filtered/incref_pc/pamir0.ply /mnt/Data2/luke/pamir/reconstructions/oneframe/Filtered/incref_pc/pamir1.ply --global-init fgr