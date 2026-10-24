"""Loopback-only QA server with an allowlisted, cached Pygbag runtime mirror."""
import argparse
import hashlib
import mimetypes
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import unquote, urlsplit
from urllib.request import urlopen

ROOT = Path(__file__).resolve().parents[2]
CACHE = ROOT / ".internal-web" / "runtime-cache"
UPSTREAM = "https://pygame-web.github.io/"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--stage", type=Path, required=True)
    parser.add_argument("--port", type=int, default=8766)
    args = parser.parse_args()
    directory = args.stage.resolve() / "build" / "web"
    if not directory.is_relative_to(ROOT / ".internal-web") or not (directory / "index.html").is_file():
        parser.error("stage must be a generated internal-web build")
    CACHE.mkdir(parents=True, exist_ok=True)

    class Handler(SimpleHTTPRequestHandler):
        def __init__(self, *a, **kw):
            super().__init__(*a, directory=str(directory), **kw)

        def end_headers(self):
            self.send_header("Access-Control-Allow-Origin", "*")
            super().end_headers()

        def do_GET(self):
            path = urlsplit(self.path).path
            if path.endswith(".apk"):
                source = (directory / unquote(path).lstrip("/")).resolve()
                if not source.is_relative_to(directory) or not source.is_file():
                    return self.send_error(404)
                size = source.stat().st_size
                header = self.headers.get("Range", "")
                start, end = 0, size - 1
                if header.startswith("bytes="):
                    first, last = header[len("bytes="):].split("-", 1)
                    if first:
                        start = int(first)
                        end = min(end, int(last)) if last else end
                    else:
                        start = max(0, size - int(last))
                if start > end or start >= size:
                    return self.send_error(416)
                self.send_response(206 if header else 200)
                self.send_header("Content-Type", "application/zip")
                self.send_header("Accept-Ranges", "bytes")
                self.send_header("Content-Length", str(end - start + 1))
                if header:
                    self.send_header("Content-Range", f"bytes {start}-{end}/{size}")
                self.end_headers()
                with source.open("rb") as stream:
                    stream.seek(start)
                    try:
                        self.wfile.write(stream.read(end - start + 1))
                    except (ConnectionResetError, ConnectionAbortedError, BrokenPipeError):
                        pass
                return
            if not path.startswith("/runtime/"):
                return super().do_GET()
            relative = unquote(path[len("/runtime/"):])
            if ".." in relative.split("/") or ":" in relative or relative.startswith("/"):
                return self.send_error(400)
            url = UPSTREAM + relative
            cached = CACHE / hashlib.sha256(url.encode()).hexdigest()
            try:
                if not cached.exists():
                    with urlopen(url, timeout=45) as response:
                        payload = response.read()
                    cached.write_bytes(payload)
                payload = cached.read_bytes()
            except Exception as error:
                print(f"Runtime fetch failed {url}: {error}", flush=True)
                return self.send_error(502, "Runtime download failed")
            self.send_response(200)
            kind = mimetypes.guess_type(relative)[0] or "application/octet-stream"
            if relative.endswith((".js", ".mjs")):
                kind = "text/javascript"
            self.send_header("Content-Type", kind)
            self.send_header("Content-Length", str(len(payload)))
            self.end_headers()
            self.wfile.write(payload)

    print(f"Private QA only: http://127.0.0.1:{args.port}", flush=True)
    ThreadingHTTPServer(("127.0.0.1", args.port), Handler).serve_forever()


if __name__ == "__main__":
    main()
