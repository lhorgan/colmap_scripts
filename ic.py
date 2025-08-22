import os

def go(image_name_to_seq):
    with open("/mnt/Data2/luke/pamir/reconstructions/oneframe/Filtered/Combined_exhaustive/sparse/text/images.txt") as f:
        read = False
        image_name = None
        image_id = None

        image_id_to_3d_points = {}

        line_num = -1
        for line in f:
            line_num += 1
            if line_num % 1000 == 0: 
                print("Reading line ", line_num)
                #break

            if line[0] == "#":
                continue
            
            if read:
                line = line.split(" ")
                point_ids = [int(point_id) for point_id in line[2::3] if int(point_id) != -1]
                #print(image_id, point_ids[0:3])
                
                image_id_to_3d_points[image_id] = {}
                image_id_to_3d_points[image_id]["points"] = point_ids
                image_id_to_3d_points[image_id]["name"] = image_name
            else:
                image_name = line.strip().split(" ")[-1]
                image_id = line.strip().split(" ")[0]

            read = not read
    
    print("Done")

    point_3d_to_image_ids = {}
    for image_id in image_id_to_3d_points:
        for point in image_id_to_3d_points[image_id]["points"]:
            if point not in point_3d_to_image_ids:
                point_3d_to_image_ids[point] = []
            point_3d_to_image_ids[point].append(image_id)
    
    seqs_for_3d_point = {}
    for point in point_3d_to_image_ids:
        #print(f"3D point {point} appears in images", point_3d_to_image_ids[point])
        for image_id in point_3d_to_image_ids[point]:
            image_name = image_id_to_3d_points[image_id]["name"]
            seq_id = image_name_to_seq[image_name]

            if point not in seqs_for_3d_point:
                seqs_for_3d_point[point] = set()

            seqs_for_3d_point[point].add(seq_id)
    
    num_1 = 0
    num_2 = 0
    num_3 = 0
    for point in seqs_for_3d_point:
        seq = seqs_for_3d_point[point]
        if len(seq) == 1:
            num_1 += 1
        elif len(seq) == 2:
            num_2 += 1
        elif len(seq) == 3:
            num_3 += 1
            #print(f"seq length for point {point}", len(seq))
    
    print(f"1 cam: {num_1}, 2 cams {num_2}, 3 cams: {num_3}, total: {len(seqs_for_3d_point)}")
        
def get_img_name_to_seq(folders):
    img_name_to_seq = {}

    for i in range(len(folders)):
        folder = folders[i]
        image_names = os.listdir(folder)
        for image_name in image_names:
            img_name_to_seq[image_name] = i
    
    return img_name_to_seq

go(get_img_name_to_seq([
    "/mnt/Data2/luke/pamir/reconstructions/oneframe/Filtered/Pamir0/Images",
    "/mnt/Data2/luke/pamir/reconstructions/oneframe/Filtered/Pamir1/Images",
    "/mnt/Data2/luke/pamir/reconstructions/oneframe/Filtered/Pamir2/Images"
]))