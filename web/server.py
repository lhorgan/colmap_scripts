# save as server.py
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse, parse_qs
import json

class Handler(BaseHTTPRequestHandler):
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
