def gen_poses_file_from_colmap_output(input_path, output_path):
    with open(input_path) as f:
        lines = f.readlines()
    
    with open(output_path, "w+") as f:
        should_skip = False
        for line in lines:
            if line[0] == "#":
                continue

            if should_skip:
                should_skip = False
            else:
                # IMAGE_ID, QW, QX, QY, QZ, TX, TY, TZ, CAMERA_ID, NAME
                line_parts = line.strip().split(" ")
                tx = float(line_parts[5])
                ty = float(line_parts[6])
                tz = float(line_parts[7])
                img_name = line_parts[9]
                print(line)

                f.write(f"{img_name} {tx} {ty} {tz}\n")
                
                should_skip = True

gen_poses_file_from_colmap_output(\
    "/home/luke/Documents/pamir_stuff/gps/gps_small_with_svin_poses_cartesian/Pamir1kf/output/sparse/0/text/images.txt", \
    "/home/luke/Documents/pamir_stuff/gps/gps_small_with_svin_poses_cartesian/Pamir1kf/output/refined_poses.txt")