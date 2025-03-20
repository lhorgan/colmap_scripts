import os
import subprocess

def go(input_path, output_path, timestamp_set):
    #biggest_timestamp = get_biggest_timestamp(input_path)
    #print("Biggest timestamp is ", biggest_timestamp)
    print("Timestamp set has length ", len(timestamp_set))

    fusion_cfg_path = os.path.join(output_path, "output/dense/stereo/fusion.cfg")
    patch_match_cfg_path = os.path.join(output_path, "output/dense/stereo/patch-match.cfg")

    if os.path.exists(fusion_cfg_path):
        print("removing ", fusion_cfg_path)
        subprocess.call(["rm", fusion_cfg_path])
    if os.path.exists(patch_match_cfg_path):
        print("removing ", patch_match_cfg_path)
        subprocess.call(["rm", patch_match_cfg_path])

    directories = [input_path]

    while len(directories) > 0:
        current_path = directories[0]
        directories = directories[1:]

        copied_path = os.path.join(output_path, current_path[len(input_path):])

        if not os.path.exists(copied_path):
            subprocess.call(["mkdir", copied_path])

        file_names = os.listdir(current_path)
        for file_name in file_names:
            file_path = os.path.join(current_path, file_name)

            print("Copying ", file_path)

            if os.path.isdir(file_path):
                directories.append(file_path)
            else:
                copy_file_path = os.path.join(copied_path, file_name)
                if not os.path.exists(copy_file_path):
                    png_ind = file_name.find(".png")
                    if png_ind >= 0:
                        timestamp = int(file_name[:png_ind])
                        if timestamp in timestamp_set:
                            subprocess.call(["cp", file_path, copy_file_path])
                    else:
                        subprocess.call(["cp", file_path, copy_file_path])

def trim_cfgs_with_set(output_path, timestamp_set):
    fusion_cfg_path = os.path.join(output_path, "output/dense/stereo/fusion.cfg")
    patch_match_cfg_path = os.path.join(output_path, "output/dense/stereo/patch-match.cfg")

    with open(patch_match_cfg_path) as f:
        lines = f.readlines()
    
    with open(patch_match_cfg_path, "w") as f:
        for i in range(0, len(lines)-1, 2):
            line = lines[i]
            timestamp = int(line.split(".")[0])
            if timestamp in timestamp_set:
                f.write(line)
                f.write(lines[i+1])
    
    with open(fusion_cfg_path) as f:
        lines = f.readlines()

    with open(fusion_cfg_path, "w") as f:
        for line in lines:
            timestamp = int(line.split(".")[0])
            if timestamp in timestamp_set:
                f.write(line)

def trim_cfgs(output_path):
    dense_maps_path = os.path.join(output_path, "output/dense/images")
    image_count = len(os.listdir(dense_maps_path))
    print("Counted ", image_count, " images.  Trimming cfgs.")
    
    fusion_cfg_path = os.path.join(output_path, "output/dense/stereo/fusion.cfg")
    patch_match_cfg_path = os.path.join(output_path, "output/dense/stereo/patch-match.cfg")

    trim_file_to_len(fusion_cfg_path, image_count)
    trim_file_to_len(patch_match_cfg_path, image_count * 2)

def trim_file_to_len(path, length):
    with open(path) as f:
        lines = f.readlines()

    with open(path, "w") as f:
        for line in lines[:length]:
            f.write(line)

def get_biggest_timestamp(input_path):
    depth_maps_path = os.path.join(input_path, "output/dense/stereo/depth_maps")
    normal_maps_path = os.path.join(input_path, "output/dense/stereo/normal_maps")

    biggest_timestamp = min(get_biggest_geometric_bin(depth_maps_path), get_biggest_geometric_bin(normal_maps_path))
    print("Biggest timestamp is ", biggest_timestamp)

    return biggest_timestamp

def get_timestamp_sets(input_path):
    depth_maps_path = os.path.join(input_path, "output/dense/stereo/depth_maps")
    normal_maps_path = os.path.join(input_path, "output/dense/stereo/normal_maps")
    depth_set = get_timestamp_set(depth_maps_path)
    norm_set = get_timestamp_set(normal_maps_path)
    return depth_set.intersection(norm_set)

def get_timestamp_set(path):
    files = [name for name in os.listdir(path) if name.endswith("geometric.bin")]
    timestamps = sorted([int(name.replace(".png.geometric.bin", "")) for name in files])
    return set(timestamps)

def get_biggest_geometric_bin(path):
    files = [name for name in os.listdir(path) if name.endswith("geometric.bin")]
    timestamps = sorted([int(name.replace(".png.geometric.bin", "")) for name in files])
    max_timestamp = timestamps[-1]
    return max_timestamp

input_fd = "/media/luke/T7/Combined2_copy/Combined_2/"
output_fd = "/home/luke/Documents/letsgo3"
timestamp_set = get_timestamp_sets(input_fd)
go(input_fd, output_fd, timestamp_set)
trim_cfgs_with_set(output_fd, timestamp_set)