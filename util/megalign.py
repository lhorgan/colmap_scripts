import sqlite3
import pickle

PROJECT_PATH = "/home/luke/pamir/Combined"
DATABASE_PATH = f"{PROJECT_PATH}/database.db"
IMAGES_PATH = f"{PROJECT_PATH}/Images"

# https://colmap.github.io/database.html#matches-and-two-view-geometries
def pair_id_to_image_ids(pair_id):
    image_id2 = pair_id % 2147483647
    image_id1 = int((pair_id - image_id2) / 2147483647)
    return image_id1, image_id2

def read_matches(database_path):
    #image_id_to_image_name, image_name_to_image_id = read_image_ids(database_path)
    image_match_info = {}

    with sqlite3.connect(database_path) as conn:
        cursor = conn.cursor()

        cursor.execute("SELECT pair_id, rows FROM two_view_geometries WHERE rows>0")

        # Define a chunk size to fetch rows in batches.
        # This is a tunable parameter; 5000 is a good starting point.
        chunk_size = 5000

        prev_image_id = -1
        while True:
            entries_batch = cursor.fetchmany(chunk_size)

            if not entries_batch:
                break

            for entry in entries_batch:
                pair_id, match_count = entry
                image_id1, image_id2 = pair_id_to_image_ids(pair_id)

                if image_id1 != prev_image_id:
                    prev_image_id = image_id1
                    print(f"Examining matches for {image_id1}")
                
                if image_id1 not in image_match_info:
                    image_match_info[image_id1] = []
                if image_id2 not in image_match_info:
                    image_match_info[image_id2] = []

                image_match_info[image_id1].append((image_id2, match_count))
                image_match_info[image_id2].append((image_id1, match_count))
    
    return image_match_info

def read_image_ids(database_path):
    image_id_to_image_name = {}
    image_name_to_image_id = {}

    with sqlite3.connect(database_path) as conn:
        cursor = conn.cursor()
        
        cursor.execute("SELECT image_id, name FROM images")
        
        rows = cursor.fetchall()

    for row in rows:
        image_id, image_name = row
        print(f"{image_id}: {image_name}")
        image_id_to_image_name[image_id] = image_name
        image_name_to_image_id[image_name] = image_id
    
    return image_id_to_image_name, image_name_to_image_id

#read_image_ids()
image_match_info = read_matches(DATABASE_PATH)
print("writing pickle")
with open("image_match_info.pkl", "wb") as f:
    pickle.dump(image_match_info, f)