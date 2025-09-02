import sqlite3

# https://colmap.github.io/database.html#matches-and-two-view-geometries
def pair_id_to_image_ids(pair_id):
    image_id2 = pair_id % 2147483647
    image_id1 = int((pair_id - image_id2) / 2147483647)
    return image_id1, image_id2

def read_matches():
    # try:
    with sqlite3.connect("/mnt/Data2/luke/pamir/reconstructions/oneframe/Filtered/Tiny/database.db") as conn:
        cursor = conn.cursor()
        
        cursor.execute("SELECT pair_id FROM two_view_geometries")

        rows = cursor.fetchall()
    # except sqlite3.Error as e:
    #     print(f"An error occurred: {e}")

    for row in rows:
        pair_id = row,
        image_id1, image_id2 = pair_id_to_image_ids(pair_id)
        print(f"{pair_id} => {image_id1}, {image_id2}")

    print(len(rows))

def read_image_ids():
    with sqlite3.connect("/mnt/Data2/luke/pamir/reconstructions/oneframe/Filtered/Tiny/database.db") as conn:
        cursor = conn.cursor()
        
        cursor.execute("SELECT image_id, name FROM images")
        
        rows = cursor.fetchall()

    for row in rows:
        image_id, image_name = row
        print(f"{image_id}: {image_name}")

read_image_ids()