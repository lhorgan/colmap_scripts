#!/usr/bin/env python3
"""
Apply a semi-random rigid transform to a point cloud (no scaling).
Useful for validating ICP: align the transformed cloud back to the original.

Usage:
  python make_transformed_clone.py cloud.ply
  # options:
  #   --angle-deg 15           Max absolute rotation angle (degrees)
  #   --trans-rel 0.05         Translation magnitude as a fraction of bbox diagonal
  #   --trans-abs 0.0          Absolute translation magnitude (overrides --trans-rel if >0)
  #   --seed 123               Random seed for reproducibility
  #   --out suffix             Filename suffix (default: _transformed)

Output:
  - Writes: <stem><suffix>.ply
  - Prints:
      * T_true (original → transformed) 4x4
      * T_inv  (transformed → original) 4x4
      * Rotation (R) and translation (t) for both
"""
import argparse
from pathlib import Path
import numpy as np
import open3d as o3d
import copy
import json

def random_unit_vector(rng):
    v = rng.normal(size=3)
    n = np.linalg.norm(v)
    return v / n if n > 0 else np.array([1.0, 0.0, 0.0])

def axis_angle_to_R(axis, angle_rad):
    ax = axis / np.linalg.norm(axis)
    x, y, z = ax
    c, s = np.cos(angle_rad), np.sin(angle_rad)
    C = 1.0 - c
    return np.array([
        [c + x*x*C,     x*y*C - z*s, x*z*C + y*s],
        [y*x*C + z*s,   c + y*y*C,   y*z*C - x*s],
        [z*x*C - y*s,   z*y*C + x*s, c + z*z*C   ]
    ])

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("cloud", type=Path)
    ap.add_argument("--angle-deg", type=float, default=15.0,
                    help="Max absolute rotation angle (degrees), sampled uniformly in [-angle, angle].")
    ap.add_argument("--trans-rel", type=float, default=0.05,
                    help="Translation magnitude as a fraction of bbox diagonal (ignored if --trans-abs>0).")
    ap.add_argument("--trans-abs", type=float, default=0.0,
                    help="Absolute translation magnitude in data units (overrides --trans-rel if >0).")
    ap.add_argument("--seed", type=int, default=None, help="Random seed for reproducibility.")
    ap.add_argument("--out", type=str, default="_transformed", help="Suffix for output filename.")
    args = ap.parse_args()

    rng = np.random.default_rng(args.seed)

    pcd = o3d.io.read_point_cloud(str(args.cloud))
    if pcd.is_empty():
        raise SystemExit("Input cloud is empty or failed to load.")

    # Scene scale (bbox diagonal)
    bounds = pcd.get_max_bound() - pcd.get_min_bound()
    diag = float(np.linalg.norm(bounds))
    if diag == 0.0:
        raise SystemExit("Input cloud has zero bounding-box diagonal (all points identical?).")

    # Random rotation
    axis = random_unit_vector(rng)
    angle = rng.uniform(-np.deg2rad(args.angle_deg), np.deg2rad(args.angle_deg))
    R = axis_angle_to_R(axis, angle)

    # Random translation
    if args.trans_abs > 0:
        t_mag = args.trans_abs
    else:
        t_mag = args.trans_rel * diag
    # Sample per-axis in [-t_mag, t_mag]
    t = rng.uniform(-t_mag, t_mag, size=3)

    # Compose homogeneous transform (original → transformed)
    T_true = np.eye(4)
    T_true[:3, :3] = R
    T_true[:3, 3] = t

    # Apply (on a copy)
    pcd_t = copy.deepcopy(pcd)
    pcd_t.transform(T_true)

    # Save
    out_path = args.cloud.with_name(f"{args.cloud.stem}{args.out}{args.cloud.suffix}")
    if not o3d.io.write_point_cloud(str(out_path), pcd_t):
        raise SystemExit(f"Failed to write output to {out_path}")

    # Inverse transform (what ICP should recover if source=transformed, target=original)
    T_inv = np.linalg.inv(T_true)
    R_inv, t_inv = T_inv[:3, :3], T_inv[:3, 3]

    # Pretty print
    np.set_printoptions(precision=6, suppress=True)
    print("\n=== Ground Truth Transform (original → transformed) ===")
    print("Rotation axis:", axis)
    print(f"Rotation angle (deg): {np.rad2deg(angle):.6f}")
    print(f"Translation t (xyz): {t}")
    print("\nT_true (4x4):\n", T_true)
    print("\nR (3x3):\n", R)
    print("\n=== Inverse Transform (transformed → original) ===")
    print("\nT_inv (4x4):\n", T_inv)
    print("\nR_inv (3x3):\n", R_inv)
    print("\nt_inv (xyz):", t_inv)
    print(f"\nWrote transformed cloud to: {out_path}")

    # Also drop a small JSON for convenience
    meta = {
        "seed": args.seed,
        "angle_deg": float(np.rad2deg(angle)),
        "axis": axis.tolist(),
        "translation": t.tolist(),
        "T_true": T_true.tolist(),
        "T_inv": T_inv.tolist(),
        "source": str(args.cloud),
        "output": str(out_path),
        "bbox_diagonal": diag,
    }
    with open(out_path.with_suffix(".json"), "w") as f:
        json.dump(meta, f, indent=2)
    print(f"Saved transform metadata: {out_path.with_suffix('.json')}")

if __name__ == "__main__":
    main()

'''
python make_transformed_clone.py \
    /mnt/Data2/luke/pamir/reconstructions/oneframe/Filtered/non_incref_point_clouds/pamir0.ply \
    --angle-deg 30 --trans-rel 0.1 --seed 7
'''