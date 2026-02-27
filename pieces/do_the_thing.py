from cluster_points import cluster_points
import open3d as o3d
import numpy as np
import math
import os

from plywood import write_point_cloud, copy_img

# arr must be sorted lowest to highest
def get_closest_timestamp(goal, timestamps):
    for i in range(len(timestamps)):
        if timestamps[i] == goal:
            return i
        elif timestamps[i] > goal:
            prev = -math.inf
            if i > 0:
                prev = timestamps[i-1]
            if (goal - prev) < (timestamps[i] - goal):
                return i - 1
            return i
    return len(timestamps) - 1

def parse_svin(svin_path):
    points = []
    quats = []
    timestamps = []

    with open(svin_path) as f:
        for line in f.readlines():
            if line.startswith("#"):
                continue
            timestamp, tx, ty, tz, qx, qy, qz, qw = line.split(" ")
            timestamp = int(timestamp.replace(".", ""))

            tx = float(tx)
            ty = float(ty)
            tz = float(tz)

            points.append([tx, ty, tz])
            quats.append([qx, qy, qz, qw])
            timestamps.append(timestamp)
    
    return points, quats, timestamps

def write_svin(points, quats, timestamps, svin_path):
    with open(svin_path) as f:
        comment = "#timestamp tx ty tz qx qy qz qw\n"
        f.write(comment)
        for i in range(len(points)):
            tx, ty, tz = timestamps[i]
            qx, qy, qz, qw = quats[i]
            line = f"{timestamps[i]} {tx} {tx} {tz} {qx} {qy} {qz} {qw}\n"
            f.write(line)

def make_fake_svins(svin_center_path, svin_left_path, svin_right_path, output_path):
    points = []
    timestamps = []

    points_c, quats_c, timestamps_c = parse_svin(svin_center_path)
    points_l, quats_l, timestamps_l = parse_svin(svin_left_path)
    points_r, quats_r, timestamps_r = parse_svin(svin_right_path)

    left_indices = [get_closest_timestamp(timestamp_l, timestamps_c) for timestamp_l in timestamps_l]
    right_indices = [get_closest_timestamp(timestamp_r, timestamps_c) for timestamp_r in timestamps_l]

    points_l_fake = [points_c[i] for i in left_indices]
    quats_l_fake = [quats_c[i] for i in left_indices]

    points_r_fake = [points_c[i] for i in right_indices]
    quats_r_fake = [quats_c[i] for i in right_indices]

    write_svin(points_c, quats_c, timestamps_c, f"{output_path}/Center.txt")
    write_svin(points_l_fake, quats_l_fake, timestamps_l, f"{output_path}/Left.txt")
    write_svin(points_r_fake, quats_r_fake, timestamps_r, f"{output_path}/Right.txt")

make_fake_svins()