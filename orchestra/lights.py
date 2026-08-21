import subprocess
import os
import argparse

from pathlib import Path

def run_colmap(data_path, scene, database_path, log_file_path):
    """
    Executes './run_colmap.sh' using the system shell to handle redirection.
    NOTE: This version does not escape arguments and assumes they are safe.
    
    Args:
        data_path (str): The path to the data directory.
        scene (str): The name of the scene.
        log_file_path (str): The path to the file for logging output.
    """
    # Construct the full command string, exactly as in the terminal
    command_string = f"./run_colmap_sphere.sh {data_path} {scene} {database_path} > {log_file_path} 2>&1"
    
    print(f"Executing via shell: {command_string}")
    
    # The shell=True argument tells subprocess to use the system's shell 
    # (like bash) to interpret the command string.
    subprocess.run(command_string, shell=True)

def reconstruct_cubes(data_path, database_path):
    cube_dirs = os.listdir(data_path)
    cube_dirs.sort(key=lambda dirname: int(dirname.split("_")[1]))
    
    for scene in cube_dirs:
        if Path(f"{data_path}/{scene}/complete.txt").is_file():
            print(f"Skipping {scene} because it is already done.")
            continue

        log_path = f"{data_path}/{scene}/log.txt"
        Path(log_path).unlink(missing_ok=True)
        Path(log_path).touch()
        run_colmap(data_path, scene, database_path, log_path)

if __name__ == "__main__":
    BASE_PATH = os.getenv("BASE_PATH", "/mnt/disk_1_ssd/luke/blub")

    parser = argparse.ArgumentParser()
    parser.add_argument("--spheres_path", type=str, default=f"{BASE_PATH}/spheres")
    parser.add_argument("--database_path", type=str, default=f"{BASE_PATH}/spheres")

    args = parser.parse_args()

    reconstruct_cubes(args.spheres_path, args.database_path)
