import sqlite3

def read_images_from_database(db_path):
    """
    Opens a SQLite database and reads the 'image_id' and 'name' fields from the 'images' table.
    
    Args:
        db_path (str): Path to the SQLite database file
        
    Returns:
        list: List of tuples containing (image_id, name) for each row
    """
    # Initialize an empty list to store the results
    image_data = []
    
    try:
        # Connect to the SQLite database
        conn = sqlite3.connect(db_path)
        
        # Create a cursor object to execute SQL queries
        cursor = conn.cursor()
        
        # Execute the SQL query to select only the fields we care about
        cursor.execute("SELECT image_id, name FROM images")
        
        # Fetch all rows and add them to our list
        image_data = cursor.fetchall()
        
        # Close the connection
        conn.close()
        
    except sqlite3.Error as e:
        print(f"Database error: {e}")
    except Exception as e:
        print(f"Exception: {e}")
        
    return image_data

def sort_images_by_id(image_tuples):
    """
    Sorts a list of image tuples (image_id, name) by their image_id in ascending order.
    
    Args:
        image_tuples (list): List of tuples containing (image_id, name)
        
    Returns:
        list: Sorted list of tuples with lowest image_id first
    """
    # Sort the list of tuples based on the first element (image_id)
    sorted_images = sorted(image_tuples, key=lambda x: x[0])
    
    return sorted_images

def verify_order(image_tuples):
    sorted_tuples = sort_images_by_id(image_tuples)
    timestamps = [int(tuple[1].replace(".png", "")) for tuple in sorted_tuples]
    timestamps = sorted(timestamps)
    
    # for i in range(len(timestamps)):
    #     comp_timestamp = int(sorted_tuples[i][1].replace(".png", ""))
    #     #print(comp_timestamp, timestamps[i])
    #     if comp_timestamp != timestamps[i]:
    #         print("woops")
    print(timestamps[0])
    print(sorted_tuples[0])


# Example usage:
#image_tuples = read_images_from_database("path/to/your/database.db")
# print(image_tuples)

image_tuples = read_images_from_database("/home/luke/Downloads/database.db")
verify_order(image_tuples)