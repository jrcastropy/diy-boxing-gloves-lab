"""Serve the Chone Fit Lab from the repo, so it can read the DXFs and save edited ones into dxf/.

Serves the whole repo (read-only) on http://localhost:PORT, so the viewer at /viewer/chone-fit-lab.html can open
dxf/*.dxf straight from the repo. The Edit pattern tab saves through POST /api/save-dxf with
{ "path": "dxf/<name>.dxf", "text": ..., "overwrite": bool }. It only writes .dxf files directly inside dxf/, refuses
to replace an existing file unless overwrite is true (409), and listens on this computer only (127.0.0.1).

Usage: python3 scripts/serve_viewer.py [PORT]    then open http://localhost:8000/viewer/chone-fit-lab.html
"""
import json
import sys
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
DXF_DIR = (REPO / "dxf").resolve()
MAX = 64 * 1024 * 1024


class Handler(SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header("Cache-Control", "no-store")  # always the file as it is on disk
        super().end_headers()

    def reply(self, code, body):
        data = json.dumps(body).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_POST(self):
        if self.path != "/api/save-dxf":
            return self.reply(404, {"error": "not found"})
        n = int(self.headers.get("Content-Length", 0))
        if not 0 < n <= MAX:
            return self.reply(400, {"error": "empty or too big"})
        try:
            req = json.loads(self.rfile.read(n))
            rel, text, overwrite = str(req["path"]), str(req["text"]), bool(req.get("overwrite"))
        except (ValueError, KeyError):
            return self.reply(400, {"error": "bad request"})
        dst = (REPO / rel).resolve()
        if dst.parent != DXF_DIR or dst.suffix.lower() != ".dxf":
            return self.reply(403, {"error": "can only save .dxf files directly inside dxf/"})
        if "SECTION" not in text or "ENTITIES" not in text:
            return self.reply(400, {"error": "that isn't a DXF"})
        if dst.exists() and not overwrite:
            return self.reply(409, {"error": "exists"})
        tmp = dst.with_name(dst.name + ".saving")
        tmp.write_text(text, newline="")
        tmp.replace(dst)
        print(f"saved {dst.relative_to(REPO)}")
        return self.reply(200, {"saved": str(dst.relative_to(REPO))})


if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8000
    srv = ThreadingHTTPServer(("127.0.0.1", port), partial(Handler, directory=str(REPO)))
    print(f"Chone Fit Lab: http://localhost:{port}/viewer/chone-fit-lab.html  (Ctrl+C to stop)")
    srv.serve_forever()
