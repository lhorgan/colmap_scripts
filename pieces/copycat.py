import os
import shutil

def main():
    plys_path = "/home/luke/Documents/caves/spheres_laptop"
    spheres_path = "/home/luke/Documents/caves/spheres"

    for scene in os.listdir(plys_path):
        scene_path = f"{plys_path}/{scene}"
        for model in os.listdir(f"{scene_path}/sparse"):
            #print(model)
            src_name = f"{scene_path}/sparse/{model}/{scene}-{model}.ply"
            dst_name = f"{spheres_path}/{scene}/sparse/{model}/{scene}-{model}.ply"
            shutil.copy2(src_name, dst_name)

if __name__ == "__main__":
    main()