# save as server.py
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse, parse_qs
from pathlib import Path
from util import load_image, annotate_points_with_crosshairs

import json, threading, time, os, cv2

def parse_points3D(directory):
    point3ds = {}   # {point3d_id: {image_id: (x, y)}}
    image_ids = {}  # {image_id: image_name}

    path = os.path.join(directory, "sparse", "text", "images.txt")
    with open(path, "r") as f:
        data_line = False
        image_name = None
        image_id = None

        line_num = -1
        for raw in f:
            line_num += 1
            if line_num % 1000 == 0:
                print("Reading line", line_num)

            s = raw.strip()
            if not s or s.startswith("#"):
                continue

            if data_line:
                parts = s.split()
                # pairs of x y point3d_id repeating
                for i in range(0, len(parts), 3):
                    try:
                        x = float(parts[i])
                        y = float(parts[i+1])
                        pid = int(parts[i+2])
                    except (IndexError, ValueError):
                        continue
                    if pid != -1:
                        if pid not in point3ds:
                            point3ds[pid] = {}
                        point3ds[pid][image_id] = (x, y)  # <-- fixed
            else:
                parts = s.split()
                # images.txt first line format starts with image_id and ends with image_name
                try:
                    image_id = int(parts[0])
                except ValueError:
                    # Fall back to raw token if not an int
                    image_id = parts[0]
                image_name = parts[-1]
                image_ids[image_id] = image_name

            data_line = not data_line

    return point3ds, image_ids

class Handler(BaseHTTPRequestHandler):
    # tiny helper for JSON responses
    def _json(self, code, payload):
        body = json.dumps(payload).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)
    
    def _resolve_image_path(self, base_dir: str, image_name: str) -> Path:
        p = Path(base_dir) / "Images" / image_name
        return p  # may or may not exist; caller will check

    def _start_background_load(self, directory):
        def worker():
            try:
                self.server.loading = True
                self.server.error = None
                pts, imgs = parse_points3D(directory)
                self.server.point3ds = pts
                self.server.image_ids = imgs
            except Exception as e:
                self.server.point3ds = None
                self.server.image_ids = None
                self.server.error = f"{type(e).__name__}: {e}"
            finally:
                self.server.loading = False

        t = threading.Thread(target=worker, daemon=True)
        t.start()
        self.server.load_thread = t

    def annotate_point(self, parsed):
        params = parse_qs(parsed.query)
        pid_raw = params.get("pointID", [None])[0]

        # Validate inputs
        if pid_raw is None:
            return self._json(400, {"ok": False, "error": "missing 'pointID' query param"})
        try:
            pid = int(pid_raw)
        except ValueError:
            return self._json(400, {"ok": False, "error": "'pointID' must be an integer"})

        # Ensure data is ready
        if not getattr(self.server, "point3ds", None) or not getattr(self.server, "image_ids", None):
            return self._json(200, {"ok": False, "status": "not_ready", "error": "points not loaded"})

        points_map = self.server.point3ds.get(pid)
        if not points_map:
            return self._json(200, {"ok": True, "status": "no_matches", "pointID": pid, "count": 0})

        base_dir = getattr(self.server, "directory", None)
        if not base_dir:
            return self._json(200, {"ok": False, "status": "not_ready", "error": "no active directory"})

        temp_root = Path(__file__).resolve().parent / "temp"
        temp_root.mkdir(parents=True, exist_ok=True)

        outputs = []
        missing = []

        for image_id, (x, y) in points_map.items():
            image_name = self.server.image_ids.get(image_id)
            if image_name is None:
                missing.append({"image_id": image_id, "reason": "name_not_found"})
                continue

            src = self._resolve_image_path(base_dir, image_name)
            if not src.exists():
                missing.append({"image_id": image_id, "image_name": image_name, "reason": f"file_not_found:{src}"})
                continue

            # Keep any subdirectory structure from image_name inside temp/
            dst = temp_root / image_name
            dst.parent.mkdir(parents=True, exist_ok=True)

            try:
                img = load_image(str(src), mode="color")
                annotated = annotate_points_with_crosshairs(img, [(x, y)])
                ok = cv2.imwrite(str(dst), annotated)
                if not ok:
                    raise RuntimeError("cv2.imwrite returned False")
            except Exception as e:
                missing.append({"image_id": image_id, "image_name": image_name, "reason": f"{type(e).__name__}: {e}"})
                continue

            outputs.append({
                "image_id": int(image_id) if isinstance(image_id, (int, float, str)) and str(image_id).isdigit() else image_id,
                "image_name": image_name,
                "dest": str(dst.relative_to(temp_root.parent))  # e.g. "temp/IMG_0001.jpg"
            })

        return self._json(200, {
            "ok": True,
            "status": "annotated",
            "pointID": pid,
            "count": len(outputs),
            "outputs": outputs,
            "missing": missing
        })

    # ---- your endpoint to poll / trigger loading ----
    def load_points(self, parsed):
        params = parse_qs(parsed.query)
        directory = params.get("directory", [None])[0]

        if not directory:
            return self._json(400, {"ok": False, "error": "missing 'directory' query param"})

        # New directory? reset state and start a fresh background load
        if directory != self.server.directory:
            self.server.directory = directory
            self.server.point3ds = None
            self.server.image_ids = None
            self.server.loading = True
            self.server.error = None
            self.server.load_started_at = time.time()
            self._start_background_load(directory)
            return self._json(200, {"ok": True, "status": "started", "directory": directory})

        # Same directory: report current status
        if self.server.loading:
            return self._json(200, {"ok": True, "status": "loading", "directory": directory})

        if self.server.error:
            return self._json(200, {"ok": False, "status": "error", "error": self.server.error, "directory": directory})

        ready = self.server.point3ds is not None and self.server.image_ids is not None
        if ready:
            return self._json(200, {
                "ok": True,
                "status": "ready",
                "directory": directory,
                "counts": {
                    "points3D": len(self.server.point3ds),
                    "images": len(self.server.image_ids)
                }
            })

        return self._json(200, {"ok": True, "status": "idle", "directory": directory})

    def do_GET(self):
        parsed = urlparse(self.path)

        if parsed.path in ("/", "/index.html"):
            try:
                with open("index.html", "rb") as fh:
                    data = fh.read()
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.send_header("Content-Length", str(len(data)))
                self.end_headers()
                self.wfile.write(data)
            except FileNotFoundError:
                self.send_error(404, "index.html not found")
            return
        elif parsed.path == "/load_points":
            self.load_points(parsed)
            return
        elif parsed.path == "/annotate_point":
            self.annotate_point(parsed)
            return
        else:
            self.send_error(404)
            return

if __name__ == "__main__":
    httpd = HTTPServer(("0.0.0.0", 8000), Handler)
    # Initialize shared state so the first request doesn't hit AttributeError
    httpd.directory = None
    httpd.point3ds = None
    httpd.image_ids = None
    httpd.loading = False
    httpd.error = None
    httpd.load_thread = None
    httpd.load_started_at = None

    httpd.serve_forever()
