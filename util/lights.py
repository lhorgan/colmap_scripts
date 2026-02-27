import subprocess
import os

from pathlib import Path

def run_colmap(data_path, scene, log_file_path):
    """
    Executes './run_colmap.sh' using the system shell to handle redirection.
    NOTE: This version does not escape arguments and assumes they are safe.
    
    Args:
        data_path (str): The path to the data directory.
        scene (str): The name of the scene.
        log_file_path (str): The path to the file for logging output.
    """
    # Construct the full command string, exactly as in the terminal
    command_string = f"./run_colmap.sh {data_path} {scene} > {log_file_path} 2>&1"
    
    print(f"Executing via shell: {command_string}")
    
    # The shell=True argument tells subprocess to use the system's shell 
    # (like bash) to interpret the command string.
    subprocess.run(command_string, shell=True)

def reconstruct_cubes(data_path):
    cube_dirs = os.listdir(data_path)
    cube_dirs.sort(key=lambda dirname: int(dirname.split("_")[1]))
    
    for scene in cube_dirs:
        if Path(f"{data_path}/{scene}/complete.txt").is_file():
            print(f"Skipping {scene} because it is already done.")
            continue

        log_path = f"{data_path}/{scene}/log.txt"
        Path(log_path).unlink(missing_ok=True)
        Path(log_path).touch()
        run_colmap(data_path, scene, log_path)

reconstruct_cubes("/home/luke/Documents/caves/spheres")