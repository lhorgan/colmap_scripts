import os
from util import *

def crayons():
    root_path = "/home/luke/Documents/caves"
    spheres_path = f"{root_path}/spheres"
    refined_path = f"{root_path}/spheres_refined_with_nloss"
    output_path = f"{root_path}/spheres_refined_with_nloss_color"

    for scene in os.listdir(spheres_path):
        scene_path = f"{spheres_path}/{scene}"
        for model in os.listdir(f"{scene_path}/sparse"):
            try:
                color_ply_name = f"{scene_path}/sparse/{model}/{scene}-{model}.ply"
                refined_ply_name = f"{refined_path}/{scene}-{model}.ply"

                color_pcd = read_point_cloud(color_ply_name)
                refined_pcd = read_point_cloud(refined_ply_name)
                refined_pcd.colors = color_pcd.colors
                write_point_cloud(refined_pcd, f"{output_path}/{scene}-{model}.ply")
            except:
                pass

if __name__ == "__main__":
    crayons()