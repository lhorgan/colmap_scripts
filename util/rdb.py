import sqlite3
import os

images_path1 = "/mnt/Data2/luke/pamir/reconstructions/oneframe/Filtered/Pamir0/Images"
images_path2 = "/mnt/Data2/luke/pamir/reconstructions/oneframe/Filtered/Pamir1/Images"
images_path3 = "/mnt/Data2/luke/pamir/reconstructions/oneframe/Filtered/Pamir2/Images"

# https://colmap.github.io/database.html#matches-and-two-view-geometries
def pair_id_to_image_ids(pair_id):
    image_id2 = pair_id % 2147483647
    image_id1 = int((pair_id - image_id2) / 2147483647)
    return image_id1, image_id2

def read_matches():
    # try:
    # with sqlite3.connect("/mnt/Data2/luke/pamir/reconstructions/oneframe/Filtered/Tiny/database.db") as conn:
    image_names = read_image_ids()
    image_name_to_seq = get_img_name_to_seq([
        images_path1,
        images_path2,
        images_path3
    ])

    # with sqlite3.connect("/mnt/Data2/luke/pamir/reconstructions/oneframe/Filtered/Combined_exhaustive/database.db") as conn:
    #     cursor = conn.cursor()

    #     # cursor.execute("SELECT COUNT(pair_id) FROM two_view_geometries")
    #     # count = cursor.fetchall()
    #     # print(f"COUNT IS {count}")
        
    #     cursor.execute("SELECT pair_id, rows FROM two_view_geometries")

    #     #rows = cursor.fetchall()

    #     matches_in_one_seq = 0
    #     matches_in_two_seq = 0

    #     prev_image_id = -1
    #     for row in cursor:
    #         pair_id, row_count = row
    #         image_id1, image_id2 = pair_id_to_image_ids(pair_id)
    #         #print(f"{pair_id} => {image_id1}, {image_id2}, {row_count}")

    #         if image_id1 != prev_image_id:
    #             prev_image_id = image_id1
    #             print(f"Examining matches for {image_id1} ({matches_in_one_seq}, {matches_in_two_seq})")

    #         image_name_1 = image_names[image_id1]
    #         image_name_2 = image_names[image_id2]

    #         seq1 = image_name_to_seq[image_name_1]
    #         seq2 = image_name_to_seq[image_name_2]
            
    #         if seq1 == seq2:
    #             matches_in_one_seq += row_count
    #         elif seq1 != seq2:
    #             matches_in_two_seq += row_count
        
    #     print(f"Matches in one seq: {matches_in_one_seq}")
    #     print(f"Matches in two seq: {matches_in_two_seq}")

    # except sqlite3.Error as e:
    #     print(f"An error occurred: {e}")

    # #print(len(rows))
    with sqlite3.connect("/mnt/Data2/luke/pamir/reconstructions/oneframe/Filtered/Combined_exhaustive/database.db") as conn:
        cursor = conn.cursor()

        cursor.execute("SELECT pair_id, rows FROM two_view_geometries")

        matches_in_one_seq = 0
        matches_in_two_seq = 0

        pairs_in_one_seq = 0
        pairs_in_two_seq = 0

        # Define a chunk size to fetch rows in batches.
        # This is a tunable parameter; 5000 is a good starting point.
        chunk_size = 5000

        prev_image_id = -1
        while True:
            # Fetch a large chunk of rows from the database
            rows_batch = cursor.fetchmany(chunk_size)

            # If the batch is empty, we've processed all rows
            if not rows_batch:
                break

            # Now, loop through the chunk that is already in memory (this part is fast)
            for row in rows_batch:
                pair_id, row_count = row
                image_id1, image_id2 = pair_id_to_image_ids(pair_id)

                if image_id1 != prev_image_id:
                    prev_image_id = image_id1
                    print(f"Examining matches for {image_id1} ({matches_in_one_seq}, {matches_in_two_seq}), ({pairs_in_one_seq}, {pairs_in_two_seq})")

                image_name_1 = image_names[image_id1]
                image_name_2 = image_names[image_id2]

                seq1 = image_name_to_seq[image_name_1]
                seq2 = image_name_to_seq[image_name_2]
                
                if seq1 == seq2:
                    matches_in_one_seq += row_count
                    pairs_in_one_seq += min(1, row_count)
                else: # Simplified from 'elif seq1 != seq2'
                    matches_in_two_seq += row_count
                    pairs_in_two_seq += min(1, row_count)
        
        print(f"Matches in one seq: {matches_in_one_seq, pairs_in_one_seq}")
        print(f"Matches in two seq: {matches_in_two_seq, pairs_in_two_seq}")

def read_image_ids():
    with sqlite3.connect("/mnt/Data2/luke/pamir/reconstructions/oneframe/Filtered/Combined_exhaustive/database.db") as conn:
        cursor = conn.cursor()
        
        cursor.execute("SELECT image_id, name FROM images")
        
        rows = cursor.fetchall()

    image_names = {}
    for row in rows:
        image_id, image_name = row
        print(f"{image_id}: {image_name}")
        image_names[image_id] = image_name

    return image_names

def get_img_name_to_seq(folders):
    img_name_to_seq = {}

    for i in range(len(folders)):
        folder = folders[i]
        print("Examining folder", folder)
        image_names = os.listdir(folder)
        for image_name in image_names:
            img_name_to_seq[image_name] = i
    
    return img_name_to_seq

# def track_matches():
#     with sqlite3.connect("/mnt/Data2/luke/pamir/reconstructions/oneframe/Filtered/Tiny/database.db") as conn:
#         cursor = conn.cursor()
        
#         cursor.execute("SELECT pair_id, rows FROM two_view_geometries")

#         rows = cursor.fetchall()
        
#     for row in rows:
#         pair_id, rows = row,
#         image_id1, image_id2 = pair_id_to_image_ids(pair_id)
#         print(f"{pair_id} => {image_id1}, {image_id2}")

#     print(len(rows))

# get_img_name_to_seq([
#     images_path1,
#     images_path2,
#     images_path3
# ])

#read_image_ids()

read_matches()

# Results:
# Examining matches for 25261 (334057061, 71960272), (1658727, 824397)
# Matches in one seq: (334057234, 1658728)
# Matches in two seq: (71960272, 824397)