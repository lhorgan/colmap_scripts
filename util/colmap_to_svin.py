def colmap_to_svin(base_path):
    svin_lines = []

    with open(f"{base_path}/sparse/text/images.txt") as f:
        data_line = True

        for line in f:
            line = line.rstrip()
            if line.startswith("#"):
                continue

            if data_line:
                image_id, qw, qx, qy, qz, tx, ty, tz, camera_id, image_name = line.split(" ")

                timestamp = f"{image_name[:10]}.{image_name[10:]}"
                #timestamp tx ty tz qx qy qz qw
                svin_line = f"{timestamp} {tx} {ty} {tz} {qx} {qy} {qz} {qw}\n"
                svin_lines.append(svin_line)

            data_line = not data_line
    
    with open(f"{base_path}/svin_from_colmap_incref.txt", "w+") as f:
        for line in svin_lines:
            f.write(line)

colmap_to_svin("/mnt/Data3/luke/underwater/onrig/Combined")