# save as server.py
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse, parse_qs
import json

def parse_points3D(directory):
    point3ds = {}
    image_ids = {}

    with open(f"{directory}/images.txt") as f:
        data_line = False
        image_name = None
        image_id = None

        image_id_to_3d_points = {}

        line_num = -1
        for line in f:
            line_num += 1
            if line_num % 1000 == 0: 
                print("Reading line ", line_num)

            if line[0] == "#":
                continue
            
            if data_line:
                line = line.split(" ")
                for ctr in range(0, len(line), 3):
                    point_x = float(line[ctr])
                    point_y = float(line[ctr+1])
                    point3d_id = int(line[ctr+2])

                    if point3d_id != -1:
                        if point3d_id not in point3ds:
                            point3ds[point3d_id] = {}
                        point3d_id[image_id] = (point_x, point_y)
                
                image_id_to_3d_points[image_id] = {}
                image_id_to_3d_points[image_id]["name"] = image_name
            else:
                image_name = line.strip().split(" ")[-1]
                image_id = line.strip().split(" ")[0]
                image_ids[image_id] = image_name

            data_line = not data_line

    return point3ds, image_ids

class Handler(BaseHTTPRequestHandler):
    def load_points(self, parsed):
        params = parse_qs(parsed.query)
        directory = params.get("directory", [None])[0]

        if directory != self.server.directory:
            # Restart the loading process
            pass
        else:
            # Indicate that the data is still loading, or that it has finished.  It has finished if the self.server.point3ds and self.server.image_ids are not None.
            pass

    def handle_point(self, parsed):
        params = parse_qs(parsed.query)
        point_id = params.get("pointID", [None])[0]

        # Always return 200 with a simple JSON body
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps({"ok": True, "pointID": point_id}).encode())

    def do_GET(self):
        parsed = urlparse(self.path)
        if parsed.path == "/point":
            self.handle_point(parsed)
        else:
            self.send_error(404)
            return

if __name__ == "__main__":
    HTTPServer(("0.0.0.0", 8000), Handler).serve_forever()
