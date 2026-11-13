"""Development web server on :3000 with transparent proxying to API :8000 and no-cache headers."""

from __future__ import annotations

import http.server
import urllib.error
import urllib.request
from pathlib import Path

WEB_DIR = Path(__file__).resolve().parent
API_TARGET = "http://127.0.0.1:8000"


class ProxyHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    """Serves static frontend files and proxies API requests to port 8000."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(WEB_DIR), **kwargs)

    def end_headers(self):
        # Force no caching in browser so updates reflect immediately
        self.send_header("Cache-Control", "no-cache, no-store, must-revalidate")
        self.send_header("Pragma", "no-cache")
        self.send_header("Expires", "0")
        super().end_headers()

    def do_POST(self):
        self._proxy_request()

    def do_GET(self):
        # If request is an API path like /v1/ or /runs, proxy it
        if self.path.startswith(("/v1/", "/runs", "/health", "/metrics")):
            self._proxy_request()
        else:
            super().do_GET()

    def _proxy_request(self):
        target_url = f"{API_TARGET}{self.path}"
        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length) if content_length > 0 else None

        req = urllib.request.Request(
            target_url,
            data=body,
            method=self.command,
        )
        for header, val in self.headers.items():
            if header.lower() not in ("host", "content-length"):
                req.add_header(header, val)

        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                self.send_response(resp.status)
                for k, v in resp.getheaders():
                    if k.lower() not in ("transfer-encoding", "content-length"):
                        self.send_header(k, v)
                resp_body = resp.read()
                self.send_header("Content-Length", str(len(resp_body)))
                self.end_headers()
                self.wfile.write(resp_body)
        except urllib.error.HTTPError as err:
            self.send_response(err.code)
            for k, v in err.headers.items():
                if k.lower() not in ("transfer-encoding", "content-length"):
                    self.send_header(k, v)
            err_body = err.read()
            self.send_header("Content-Length", str(len(err_body)))
            self.end_headers()
            self.wfile.write(err_body)
        except Exception as e:
            self.send_response(502)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(f'{{"error": "Proxy error", "detail": "{str(e)}"}}'.encode("utf-8"))


if __name__ == "__main__":
    server = http.server.ThreadingHTTPServer(("0.0.0.0", 3000), ProxyHTTPRequestHandler)
    print(f"Serving on http://0.0.0.0:3000 with API proxy to {API_TARGET}")
    server.serve_forever()

