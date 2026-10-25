"""The pantry web app: a page and a small JSON API over store.py."""
import json, os, re
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

import store

STATIC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static")
ITEM_ACTION = re.compile(r"^/api/items/(\d+)/(use|restock)$")


class Handler(BaseHTTPRequestHandler):
    def _send(self, code, body, kind="application/json"):
        raw = body if isinstance(body, bytes) else json.dumps(body).encode()
        self.send_response(code)
        self.send_header("Content-Type", kind)
        self.send_header("Content-Length", str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)

    def _static(self, name, kind):
        with open(os.path.join(STATIC, name), "rb") as fh:
            self._send(200, fh.read(), kind)

    def _body(self):
        length = int(self.headers.get("Content-Length") or 0)
        return json.loads(self.rfile.read(length) or b"{}")

    def do_GET(self):
        url = urlparse(self.path)
        if url.path == "/":
            return self._static("index.html", "text/html")
        if url.path == "/app.js":
            return self._static("app.js", "text/javascript")
        if url.path == "/api/items":
            data = store.load()
            q = parse_qs(url.query).get("q", [""])[0]
            return self._send(200, store.search(data, q) if q else data["items"])
        if url.path == "/api/shopping-list":
            return self._send(200, store.shopping_list(store.load()))
        if url.path == "/api/stats":
            return self._send(200, store.stats(store.load()))
        if url.path == "/debug/dump" and os.environ.get("PANTRY_DEBUG"):
            return self._send(200, store.load())
        self._send(404, {"error": "not found"})

    def do_POST(self):
        url = urlparse(self.path)
        if url.path == "/api/items":
            b = self._body()
            item = store.add_item(b["name"], int(b["qty"]), int(b.get("min", 1)), b.get("unit", "pcs"))
            return self._send(201, item)
        m = ITEM_ACTION.match(url.path)
        if m:
            item_id, action = int(m.group(1)), m.group(2)
            n = int(self._body().get("n", 1))
            try:
                item = store.use_item(item_id, n) if action == "use" else store.restock(item_id, n)
            except (KeyError, ValueError) as exc:
                return self._send(400, {"error": str(exc)})
            return self._send(200, item)
        self._send(404, {"error": "not found"})


def serve(port=8040):
    httpd = ThreadingHTTPServer(("127.0.0.1", port), Handler)
    print(f"pantry on http://127.0.0.1:{port}")
    httpd.serve_forever()
