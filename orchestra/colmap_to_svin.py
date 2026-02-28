def colmap_to_svin(input_path, output_path):
    svin_lines = []
    image_names = set()

    with open(input_path) as f:
        data_line = True

        for line in f:
            line = line.rstrip()
            if line.startswith("#"):
                continue

            if data_line:
                image_id, qw, qx, qy, qz, tx, ty, tz, camera_id, image_name = line.split(" ")
                timestamp = f"{image_name[:10]}.{image_name[10:-4]}"

                image_names.add(image_name)
                
                #timestamp tx ty tz qx qy qz qw
                svin_line = f"{timestamp} {tx} {ty} {tz} {qx} {qy} {qz} {qw}\n"
                svin_lines.append(svin_line)
                #print(svin_line)

            data_line = not data_line
    
    print("WRITING TO ", output_path)

    with open(output_path, "w+") as f:
        comment = "#timestamp tx ty tz qx qy qz qw\n"
        f.write(comment)
        for line in svin_lines:
            f.write(line)

    return image_names