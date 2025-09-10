#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Aug 29 19:01:47 2025

@author: harish
"""

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Aug 29 16:49:04 2025

@author: harish
"""

import numpy as np
import argparse
from typing import Tuple, Dict
import open3d as o3d
import copy
import os

def quat_to_rotmat_batch(q: np.ndarray) -> np.ndarray:
    """
    Convert batched quaternions (N,4) [qx,qy,qz,qw] (scalar last) to rotation matrices (N,3,3).
    Assumes input quaternions are normalized. Vectorized.
    """
    q = np.asarray(q, dtype=np.float64)
    assert q.ndim == 2 and q.shape[1] == 4, "q must be (N,4) with [qx,qy,qz,qw]"
    x, y, z, w = q[:, 0], q[:, 1], q[:, 2], q[:, 3]

    xx, yy, zz = x*x, y*y, z*z
    xy, xz, yz = x*y, x*z, y*z
    wx, wy, wz = w*x, w*y, w*z

    R = np.empty((q.shape[0], 3, 3), dtype=np.float64)
    R[:, 0, 0] = 1 - 2*(yy + zz)
    R[:, 0, 1] = 2*(xy - wz)
    R[:, 0, 2] = 2*(xz + wy)

    R[:, 1, 0] = 2*(xy + wz)
    R[:, 1, 1] = 1 - 2*(xx + zz)
    R[:, 1, 2] = 2*(yz - wx)

    R[:, 2, 0] = 2*(xz - wy)
    R[:, 2, 1] = 2*(yz + wx)
    R[:, 2, 2] = 1 - 2*(xx + yy)
    return R

def read_trajectory_txt(path: str, sort_by_time: bool = True):
    """
    Reads lines: timestamp tx ty tz qx qy qz qw
    Returns:
      t_str : list of exact timestamp strings (preserves all digits)
      t_ns  : (N,) int64 nanoseconds since epoch (exact, good for sorting/math)
      t     : (N,) float64 seconds (approximate, convenient)
      xyz   : (N,3) float64
      q     : (N,4) float64 [qx,qy,qz,qw] (unit, qw>=0)
      R     : (N,3,3) float64
      T     : (N,4,4) float64
    """
    times_str, times_ns, xyzs, quats = [], [], [], []
    with open(path, 'r', encoding='utf-8') as f:
        for idx, raw in enumerate(f, 1):
            line = raw.strip()
            if not line:
                continue
            for cmt in ('#', '//'):
                if cmt in line:
                    line = line.split(cmt, 1)[0].strip()
            if not line:
                continue
            parts = line.replace(',', ' ').split()
            if len(parts) != 8:
                raise ValueError(f"{path}:{idx}: expected 8 fields, got {len(parts)}")
            t_tok, tx, ty, tz, qx, qy, qz, qw = parts
            times_str.append(t_tok)
            times_ns.append(_parse_timestamp_to_ns(t_tok))
            xyzs.append([float(tx), float(ty), float(tz)])
            quats.append([float(qx), float(qy), float(qz), float(qw)])

    t_ns = np.asarray(times_ns, dtype=np.int64)
    t = t_ns.astype(np.float64) / 1e9  # convenient float version (approximate)
    xyz = np.asarray(xyzs, dtype=np.float64)
    q = np.asarray(quats, dtype=np.float64)

    # Normalize quats, enforce qw >= 0
    q /= np.maximum(np.linalg.norm(q, axis=1, keepdims=True), 1e-12)
    flip = q[:, 3] < 0
    q[flip] *= -1

    # Quaternion -> rotation matrices
    x, y, z, w = q[:,0], q[:,1], q[:,2], q[:,3]
    xx, yy, zz = x*x, y*y, z*z
    xy, xz, yz = x*y, x*z, y*z
    wx, wy, wz = w*x, w*y, w*z
    R = np.empty((q.shape[0], 3, 3), dtype=np.float64)
    R[:,0,0] = 1 - 2*(yy + zz);  R[:,0,1] = 2*(xy - wz);      R[:,0,2] = 2*(xz + wy)
    R[:,1,0] = 2*(xy + wz);      R[:,1,1] = 1 - 2*(xx + zz);  R[:,1,2] = 2*(yz - wx)
    R[:,2,0] = 2*(xz - wy);      R[:,2,1] = 2*(yz + wx);      R[:,2,2] = 1 - 2*(xx + yy)

    # Build SE(3) poses
    N = len(times_str)
    T = np.repeat(np.eye(4, dtype=np.float64)[None, ...], N, axis=0)
    T[:, :3, :3] = R
    T[:, :3,  3] = xyz

    if sort_by_time:
        order = np.argsort(t_ns)
        t_ns, t, xyz, q, R, T = t_ns[order], t[order], xyz[order], q[order], R[order], T[order]
        times_str = [times_str[i] for i in order]

    return {
        't_str': times_str,  # exact, for writing back losslessly
        't_ns': t_ns,        # exact integer nanoseconds
        't': t,              # approximate float seconds
        'xyz': xyz,
        'quat_xyzw': q,
        'R': R,
        'T': T,
    }

def _parse_timestamp_to_ns(tok: str) -> int:
    """
    Parse 'seconds[.fraction]' into integer nanoseconds exactly.
    Handles variable-length fraction and negatives.
    """
    s = tok.strip()
    neg = s.startswith('-')
    if neg: s = s[1:]
    if '.' in s:
        a, b = s.split('.', 1)
        b_digits = ''.join(ch for ch in b if ch.isdigit())
        if len(b_digits) > 9:
            # round to 9 digits (ns) instead of truncating
            frac_rounded = int(round(int(b_digits[:10]) / 10.0))  # round at 9th place
            if frac_rounded == 10**9:
                sec = int(a) + 1
                frac_ns = 0
            else:
                sec = int(a)
                frac_ns = frac_rounded
        else:
            sec = int(a) if a else 0
            frac_ns = int(b_digits.ljust(9, '0')) if b_digits else 0
    else:
        sec = int(s) if s else 0
        frac_ns = 0
    total = sec * 1_000_000_000 + frac_ns
    return -total if neg else total

def _ns_to_timestamp_str(ns: int) -> str:
    """Reconstruct 'sec.nnnnnnnnn' from integer nanoseconds exactly (keeps sign correct)."""
    if ns >= 0:
        sec = ns // 1_000_000_000
        rem = ns - sec * 1_000_000_000
        return f"{sec}.{rem:09d}"
    v = -ns
    sec = v // 1_000_000_000
    rem = v - sec * 1_000_000_000
    return f"-{sec}.{rem:09d}"

def apply_rigid_to_trajectory(T, centers, rotations, reproject=True):
    """
    Apply a single rigid-body transform T (4x4) to a trajectory given by:
      centers  : (N, 3) camera centers (points in the old world frame)
      rotations: (N, 3, 3) camera orientation matrices (camera axes expressed in old world)

    Assumes T maps old-world coordinates to new-world coordinates:
      X_new = R_T @ X_old + t_T,
      with T = [[R_T, t_T],
                [  0 ,  1 ]]

    Then the transformed trajectory in the new world frame is:
      centers'   = R_T @ centers + t_T
      rotations' = R_T @ rotations

    If your T goes the other way (new→old), pass np.linalg.inv(T).

    Set reproject=True to project rotations back to SO(3) via batched SVD.
    """
    T = np.asarray(T, dtype=np.float64)
    C = np.asarray(centers, dtype=np.float64)
    R = np.asarray(rotations, dtype=np.float64)

    assert T.shape == (4, 4), "T must be 4x4"
    assert C.ndim == 2 and C.shape[1] == 3, "centers must be (N,3)"
    assert R.ndim == 3 and R.shape[1:] == (3, 3), "rotations must be (N,3,3)"

    R_T = T[:3, :3]
    t_T = T[:3, 3]

    # Centers: point transform
    C_new = C @ R_T.T + t_T  # (N,3)

    # Rotations: change of world frame (rotate camera axes expressed in world)
    R_new = R_T[None, :, :] @ R  # (N,3,3)

    if reproject:
        # Project to the closest rotation (det=+1) via SVD
        U, _, Vt = np.linalg.svd(R_new)
        R_new = U @ Vt
        dets = np.linalg.det(R_new)
        bad = dets < 0
        if np.any(bad):
            U[bad, :, -1] *= -1.0
            R_new[bad] = U[bad] @ Vt[bad]

    return C_new, R_new

def write_trajectory_txt(path: str, t: np.ndarray, xyz: np.ndarray, q: np.ndarray) -> None:
    """Writes: timestamp tx ty tz qx qy qz qw"""
    with open(path, 'w', encoding='utf-8') as f:
        for i in range(len(t)):
            f.write(f"{t[i]} {xyz[i,0]:.9f} {xyz[i,1]:.9f} {xyz[i,2]:.9f} "
                    f"{q[i,0]:.9f} {q[i,1]:.9f} {q[i,2]:.9f} {q[i,3]:.9f}\n")

def rotmat_to_quat_batch(R: np.ndarray) -> np.ndarray:
    """(N,3,3) -> [qx,qy,qz,qw], vectorized, robust branch on trace."""
    R = np.asarray(R, dtype=np.float64)
    N = R.shape[0]
    q = np.empty((N, 4), dtype=np.float64)
    tr = R[:,0,0] + R[:,1,1] + R[:,2,2]
    # Case 1: trace positive
    mask0 = tr > 0
    s0 = np.sqrt(tr[mask0] + 1.0) * 2.0
    q[mask0, 3] = 0.25 * s0
    q[mask0, 0] = (R[mask0, 2,1] - R[mask0, 1,2]) / s0
    q[mask0, 1] = (R[mask0, 0,2] - R[mask0, 2,0]) / s0
    q[mask0, 2] = (R[mask0, 1,0] - R[mask0, 0,1]) / s0
    # Case 2+: pick largest diagonal
    mask1 = ~mask0
    if np.any(mask1):
        Rm = R[mask1]
        q1 = np.empty((Rm.shape[0], 4), dtype=np.float64)
        idx = np.argmax(np.stack([Rm[:,0,0], Rm[:,1,1], Rm[:,2,2]], axis=1), axis=1)
        for i in range(Rm.shape[0]):
            Ri = Rm[i]
            k = idx[i]
            if k == 0:
                s = np.sqrt(1.0 + Ri[0,0] - Ri[1,1] - Ri[2,2]) * 2.0
                q1[i,0] = 0.25 * s
                q1[i,1] = (Ri[0,1] + Ri[1,0]) / s
                q1[i,2] = (Ri[0,2] + Ri[2,0]) / s
                q1[i,3] = (Ri[2,1] - Ri[1,2]) / s
            elif k == 1:
                s = np.sqrt(1.0 - Ri[0,0] + Ri[1,1] - Ri[2,2]) * 2.0
                q1[i,0] = (Ri[0,1] + Ri[1,0]) / s
                q1[i,1] = 0.25 * s
                q1[i,2] = (Ri[1,2] + Ri[2,1]) / s
                q1[i,3] = (Ri[0,2] - Ri[2,0]) / s
            else:
                s = np.sqrt(1.0 - Ri[0,0] - Ri[1,1] + Ri[2,2]) * 2.0
                q1[i,0] = (Ri[0,2] + Ri[2,0]) / s
                q1[i,1] = (Ri[1,2] + Ri[2,1]) / s
                q1[i,2] = 0.25 * s
                q1[i,3] = (Ri[1,0] - Ri[0,1]) / s
        q[mask1] = q1
    # Normalize and enforce qw >= 0 for sign consistency
    q /= np.linalg.norm(q, axis=1, keepdims=True)
    flip = q[:,3] < 0
    q[flip] *= -1
    return q

# -------- Example usage --------

### traj_path expects svin style txt file of trajectories
### T is a 4x4 transform matrix (with 4th row being 0,0,0,1)
### traj_path_out is the path to write the transformed trajectories to (svin format)
def get_transformed_pts(traj_path, T, traj_path_out):
    
    traj_dict = read_trajectory_txt(traj_path, sort_by_time=False)
    
    centers = traj_dict["xyz"]
    rots = traj_dict["R"]
    timestamps = traj_dict["t_str"]

    C_new, R_new = apply_rigid_to_trajectory(T, centers, rots, reproject=True)
        
    q_new = rotmat_to_quat_batch(R_new)
    write_trajectory_txt(traj_path_out, timestamps, C_new, q_new)


# transform = np.array([[0.999453, -0.018089, 0.027675, 3.413445], 
#                       [0.018029, 0.999835, 0.002422, 0.912243], 
#                       [-0.027714, -0.001922,  0.999614, 0.187898], 
#                       [0, 0, 0, 1]])

# input_path = "/mnt/Data2/luke/pamir/reconstructions/oneframe/Pamir/Pamir2/Pamir2_transformed_backup.txt"
# output_path = "/mnt/Data2/luke/pamir/reconstructions/oneframe/Pamir/Pamir2/Pamir2_in_Pamir1.txt"

# get_transformed_pts(input_path, transform, output_path)

transform = np.array([[ 0.999388,  0.009151, -0.033753, -0.384451],
                      [-0.01022,   0.999447, -0.031629, -0.578503],
                      [0.033445,  0.031954,  0.99893,  -0.084902],
                      [0, 0, 0, 1]])

input_path = "/mnt/Data3/luke/underwater/reconstructions/Pamir2/svin_orig.txt"
output_path = "/mnt/Data3/luke/underwater/reconstructions/Pamir2/svin_orig_transformed.txt"

get_transformed_pts(input_path, transform, output_path)
    