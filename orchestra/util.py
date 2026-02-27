import open3d as o3d
import numpy as np
#import itertools
import copy
import shutil

from pathlib import Path

def copy_img(src_path, dst_path):
    Path(dst_path).parent.mkdir(parents=True, exist_ok=True)
    shutil.copy(src_path, dst_path)

def read_point_cloud(file_path):
    """Read a point cloud from file"""
    return o3d.io.read_point_cloud(file_path)

def write_point_cloud(point_cloud, file_path):
    """Write the point cloud to the file path specified"""
    o3d.io.write_point_cloud(file_path, point_cloud)