"""A tiny notes service: the product the create-mode example verifies. Stdlib only."""
import argparse, hashlib, json, os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

SOURCE = os.path.abspath(__file__)


def build_id():
    with open(SOURCE, "rb") as fh:
        return hashlib.sha256(fh.read()).hexdigest()[:16]


class Notes(BaseHTTPRequestHandler):
    def _send(self, code, body):
        data = json.dumps(body).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def _load(self):
        with open(self.server.store, encoding="utf-8") as fh:
            return json.load(fh)

    def do_GET(self):
        if self.path == "/health":
            return self._send(200, {"ok": True, "build": self.server.build, "pid": os.getpid(),
                                    "data": self.server.store})
        if self.path == "/notes":
            return self._send(200, self._load())
        self._send(404, {"error": "not found"})

    def do_POST(self):
        if self.path != "/notes":
            return self._send(404, {"error": "not found"})
        body = json.loads(self.rfile.read(int(self.headers.get("Content-Length", 0))) or b"{}")
        title = str(body.get("title", "")).strip()
        if not title:
            return self._send(400, {"error": "title required"})
        notes = self._load()
        note = {"id": len(notes) + 1, "title": title, "body": str(body.get("body", ""))}
        notes.append(note)
        with open(self.server.store, "w", encoding="utf-8") as fh:
            json.dump(notes, fh)
        self._send(201, note)

    def log_message(self, *args):
        pass


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", type=int, default=8765)
    ap.add_argument("--data", default=".verify-data")
    a = ap.parse_args()
    server = ThreadingHTTPServer(("127.0.0.1", a.port), Notes)
    server.store = os.path.abspath(os.path.join(a.data, "notes.json"))
    server.build = build_id()
    print(f"notes listening on 127.0.0.1:{a.port} build {server.build}", flush=True)
    server.serve_forever()


if __name__ == "__main__":
    main()
