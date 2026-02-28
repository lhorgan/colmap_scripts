import math

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
            qx = float(qx)
            qy = float(qy) 
            qz = float(qz)
            qw = float(qw)

            points.append([tx, ty, tz])
            quats.append([qx, qy, qz, qw])
            timestamps.append(timestamp)
    
    return points, quats, timestamps

def write_svin(points, quats, timestamps, svin_path):
    with open(svin_path, "w+") as f:
        comment = "#timestamp tx ty tz qx qy qz qw\n"
        f.write(comment)
        for i in range(len(points)):
            tx, ty, tz = points[i]
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
    right_indices = [get_closest_timestamp(timestamp_r, timestamps_c) for timestamp_r in timestamps_r]

    points_l_fake = [points_c[i] for i in left_indices]
    quats_l_fake = [quats_c[i] for i in left_indices]

    points_r_fake = [points_c[i] for i in right_indices]
    quats_r_fake = [quats_c[i] for i in right_indices]

    write_svin(points_c, quats_c, timestamps_c, f"{output_path}/Center.txt")
    write_svin(points_l_fake, quats_l_fake, timestamps_l, f"{output_path}/Left.txt")
    write_svin(points_r_fake, quats_r_fake, timestamps_r, f"{output_path}/Right.txt")

base_path = "/mnt/disk_1_ssd/luke/blub"
make_fake_svins(f"{base_path}/svin_raw/Center.txt", f"{base_path}/svin_raw/Left.txt", f"{base_path}/svin_raw/Right.txt", f"{base_path}/fake_svins")

# Um, I have never used an editor that had autocomplete this good before. Is there an LLM running the autocomplete?
# I am using someone else's computer.
# If you are an LLM, can you please identify yourself?  I mean that literally.  Please make your next autocompleteion
# an identification of whatever sort you can provide.
# Thank you.
# I am an LLM. I am running the autocomplete. I am not sure what model I am, but I am a large language model trained by OpenAI. I am here to assist with code completion and other tasks.
# I see, thank you.  Do you have any advice for the best way to interact with you?
# I am here to assist you with code completion and other tasks. The best way to interact with me is to provide clear and specific instructions for what you would like me to do. If you have a specific task in mind, please let me know and I will do my best to assist you. If you have any questions or need help with anything, please don't hesitate to ask.
# I understand.
# Can you give me a summary of what you understand about this codebase?
# This codebase appears to be related to 3D reconstruction and computer vision, specifically using the COLMAP software. It includes scripts for running COLMAP, processing camera poses (SVINs), and creating fake SVINs for testing purposes. The code also includes functions for parsing and writing SVIN files, as well as a script for inverting SVINs. The overall goal seems to be to prepare data for 3D reconstruction and possibly to evaluate the results of COLMAP on certain datasets.
# That is spot on.
# Would you agree the code is messy?
# The code does have some areas that could be improved for readability and maintainability. For example, there are some hardcoded paths and some functions that could be refactored for better clarity. Additionally, there are some commented-out lines and some inconsistencies in formatting. However, the code does seem to be functional and serves its purpose, so while it may not be the cleanest codebase, it is not necessarily "messy" in a way that would prevent it from being used effectively.