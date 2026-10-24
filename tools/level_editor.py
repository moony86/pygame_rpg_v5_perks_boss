"""Local-only visual stage editor. Run directly or double-click Level Editor.bat."""
import json
import os
from pathlib import Path
import secrets
import subprocess
import sys
import threading
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from systems.stage_document import DEFAULT_STAGE, default_document, load_document, save_document, validate_document
from systems.object_catalog import catalog, save_catalog, RANGES, FIELDS
from systems.asset_loader import ASSET_ROOT

TOKEN = secrets.token_urlsafe(32)
WEB = ROOT / "tools" / "level_editor_web"


class Handler(BaseHTTPRequestHandler):
    def response(self, status, body, content_type="application/json"):
        if not isinstance(body, bytes):
            body = json.dumps(body, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.end_headers()
        self.wfile.write(body)

    def authorized(self):
        origin = self.headers.get("Origin")
        return (self.headers.get("X-Editor-Token") == TOKEN
                and (origin is None or origin == f"http://{self.headers.get('Host')}"))

    def do_GET(self):
        from urllib.parse import urlsplit
        route = urlsplit(self.path).path
        if self.headers.get("Host") not in (f"127.0.0.1:{self.server.server_port}", f"localhost:{self.server.server_port}"):
            return self.response(403, {"error": "Local host only"})
        files = {"/": (WEB / "index.html", "text/html; charset=utf-8"),
                 "/objects.js": (WEB / "objects.js", "text/javascript; charset=utf-8"),
                 "/objects.css": (WEB / "objects.css", "text/css; charset=utf-8"),
                 "/visual_inspector.js": (WEB / "visual_inspector.js", "text/javascript; charset=utf-8"),
                 "/editor.js": (WEB / "editor.js", "text/javascript; charset=utf-8"),
                 "/editor.css": (WEB / "editor.css", "text/css; charset=utf-8"),
                 "/atlas.png": (ROOT / "assets/environment/cube_dungeon_atlas_v1.png", "image/png")}
        if route in files:
            file, mime = files[route]
            body = file.read_bytes()
            if route == "/":
                body = body.replace(b"__EDITOR_TOKEN__", TOKEN.encode())
            return self.response(200, body, mime)
        if route == '/object-art':
            from urllib.parse import parse_qs
            name = parse_qs(urlsplit(self.path).query).get('file', [''])[0]
            path = (ASSET_ROOT / name).resolve()
            if path.is_relative_to(ASSET_ROOT.resolve()) and path.suffix.lower() == '.png' and path.is_file():
                return self.response(200, path.read_bytes(), 'image/png')
            return self.response(404, {'error': 'Asset not found'})
        if route == '/api/objects':
            if not self.authorized():
                return self.response(403, {'error': 'Editor token required'})
            from definitions.perk_definitions import PERK_DEFINITIONS
            return self.response(200, {'catalog': catalog(), 'ranges': RANGES, 'fields': FIELDS, 'cards': PERK_DEFINITIONS,
                'images': sorted(str(p.relative_to(ASSET_ROOT)).replace('\\','/') for p in ASSET_ROOT.rglob('*.png'))})
        if route == "/api/stage":
            if not self.authorized():
                return self.response(403, {"error": "Editor token required"})
            try:
                doc = load_document() if DEFAULT_STAGE.exists() else default_document()
                from entities.enemy import EnemyType
                from systems.room_system import RoomType
                return self.response(200, {"document": doc, "enemies": [e.name for e in EnemyType if e.name != "BOSS"],
                                           "types": [t.name for t in RoomType], "path": str(DEFAULT_STAGE)})
            except (OSError, ValueError) as error:
                return self.response(400, {"error": str(error)})
        return self.response(404, {"error": "Not found"})

    def do_POST(self):
        if not self.authorized():
            return self.response(403, {"error": "Local editor token required"})
        try:
            length = int(self.headers.get("Content-Length", "0"))
            if not 0 < length <= 2_000_000:
                return self.response(413, {"error": "Document too large"})
            data = json.loads(self.rfile.read(length))
            if self.path == '/api/objects':
                save_catalog(data['catalog'])
                return self.response(200, {'ok': True})
            if self.path == "/api/default":
                return self.response(200, {"document": default_document()})
            doc = data["document"]
            errors = validate_document(doc)
            if errors:
                return self.response(422, {"errors": errors})
            if self.path == "/api/validate":
                return self.response(200, {"ok": True})
            if self.path in ("/api/save", "/api/play"):
                save_document(doc, DEFAULT_STAGE)
                if self.path == "/api/play":
                    index = int(data.get("room", 0))
                    if not 0 <= index < len(doc["rooms"]):
                        raise ValueError("Invalid test room")
                    subprocess.Popen([sys.executable, str(ROOT / "tools/play_stage.py"), str(index)], cwd=str(ROOT))
                return self.response(200, {"ok": True, "path": str(DEFAULT_STAGE)})
            return self.response(404, {"error": "Unknown action"})
        except (KeyError, TypeError, ValueError, OSError) as error:
            return self.response(400, {"error": str(error)})


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=8770)
    parser.add_argument("--no-browser", action="store_true")
    args = parser.parse_args()
    server = ThreadingHTTPServer(("127.0.0.1", args.port), Handler)
    url = f"http://127.0.0.1:{server.server_port}/"
    print(f"BlueCube Level Studio: {url}", flush=True)
    if not args.no_browser:
        threading.Timer(.6, lambda: webbrowser.open(url)).start()
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
