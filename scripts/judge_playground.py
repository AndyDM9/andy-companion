"""Run the isolated guided judge playground. No household settings are loaded.

Set JUDGE_NEBIUS_API_KEY on the server, never in the page or a command argument.
With no key the page remains available and clearly reports that inference is off.
"""
from __future__ import annotations

from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import os
from pathlib import Path
import sys
import threading
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from andy_companion.judge_playground import Playground, Unavailable  # noqa: E402


def server(engine, address=("127.0.0.1", 8096), public_origin=""):
    pages = ROOT / "src/andy_companion/pages"
    assets = {"/": (pages / "judge.html", "text/html; charset=utf-8"),
              "/fonts/atkinson-hyperlegible-400.woff2": (pages / "fonts/atkinson-hyperlegible-400.woff2", "font/woff2"),
              "/fonts/atkinson-hyperlegible-700.woff2": (pages / "fonts/atkinson-hyperlegible-700.woff2", "font/woff2"),
              "/judge.js": (pages / "judge.js", "text/javascript; charset=utf-8")}

    class Handler(BaseHTTPRequestHandler):
        def setup(self):
            super().setup()
            self.connection.settimeout(5)

        def log_message(self, *args):
            pass  # No request paths, bodies, provider errors or model text in logs.

        def _send(self, code, value, content_type="application/json; charset=utf-8"):
            data = value if isinstance(value, bytes) else json.dumps(value).encode()
            self.send_response(code)
            for name, field in {"Content-Type": content_type, "Content-Length": str(len(data)),
                                "Cache-Control": "no-store", "X-Content-Type-Options": "nosniff",
                                "Referrer-Policy": "no-referrer", "Permissions-Policy": "camera=(), microphone=()",
                                "Content-Security-Policy": "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; "
                                "connect-src 'self'; frame-ancestors 'self' https://huggingface.co; base-uri 'none'; form-action 'none'"}.items():
                self.send_header(name, field)
            self.end_headers()
            self.wfile.write(data)

        def do_GET(self):
            if self.path == "/api/status":
                return self._send(200, engine.metadata())
            if self.path in assets:
                path, kind = assets[self.path]
                return self._send(200, path.read_bytes(), kind)
            self._send(404, {"error": "not_found"})

        def do_POST(self):
            if self.path != "/api/run":
                return self._send(404, {"error": "not_found"})
            origin = self.headers.get("Origin")
            local_origin = f"http://{self.headers.get('Host', '')}"
            allowed = {public_origin} if public_origin else {local_origin}
            if (origin and origin not in allowed) or self.headers.get("Sec-Fetch-Site") == "cross-site":
                return self._send(403, {"error": "same_origin_only"})
            if self.headers.get("Content-Type", "").split(";", 1)[0].strip() != "application/json":
                return self._send(415, {"error": "json_required"})
            try:
                size = int(self.headers.get("Content-Length", "0"))
                if not 0 < size <= 512 or self.headers.get("Transfer-Encoding"):
                    return self._send(413, {"error": "request_too_large"})
                raw = self.rfile.read(size)
                if len(raw) != size:
                    raise ValueError()
                body = json.loads(raw)
            except (ValueError, OSError):
                return self._send(400, {"error": "invalid_request"})
            try:
                result = engine.run(body)
            except Unavailable as error:
                return self._send(error.status, {"error": error.code})
            except Exception:
                return self._send(503, {"error": "challenge_unavailable"})
            self._send(200, result)

    class Server(ThreadingHTTPServer):
        daemon_threads = True

        def __init__(self, *args):
            self.slots = threading.BoundedSemaphore(16)
            super().__init__(*args)

        def process_request(self, request, client_address):
            if not self.slots.acquire(blocking=False):
                self.shutdown_request(request)
                return
            try:
                super().process_request(request, client_address)
            except Exception:
                self.slots.release()
                raise

        def process_request_thread(self, request, client_address):
            try:
                super().process_request_thread(request, client_address)
            finally:
                self.slots.release()

        def service_actions(self):
            engine.expire()

        def handle_error(self, request, client_address):
            pass  # Includes disconnects; tracebacks must not contain request/model data.

    return Server(address, Handler)


def main():
    if "--help" in sys.argv[1:]:
        print(__doc__)
        return
    origin = os.environ.get("JUDGE_PUBLIC_ORIGIN", "")
    if origin and (urlsplit(origin).scheme != "https" or urlsplit(origin).path not in ("", "/")):
        raise SystemExit("JUDGE_PUBLIC_ORIGIN must be an HTTPS origin")
    engine = Playground(profile_path=ROOT / "profiles/companion/profile.md", tools_path=ROOT / "evals/tools.json",
                        key=os.environ.get("JUDGE_NEBIUS_API_KEY", ""))
    port = int(os.environ.get("PORT", "8096"))
    httpd = server(engine, ("0.0.0.0" if origin else "127.0.0.1", port), origin.rstrip("/"))
    print(f"Judge playground ready on port {port}; inference {'enabled' if engine.key else 'off'}.", flush=True)
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        httpd.server_close()


if __name__ == "__main__":
    main()
