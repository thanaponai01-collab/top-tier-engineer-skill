"""Tiny live application that reports the source and runtime contract it loaded."""
import hashlib
import json
import os
import sys
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path


def identity():
    settings = json.loads(Path("config.json").read_text(encoding="utf-8"))
    source = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    return {
        "source_sha256": source,
        "config_sha256": hashlib.sha256(Path("config.json").read_bytes()).hexdigest(),
        "flags": settings["flags"],
        "role": settings["role"],
        "mocks": settings["mocks"],
        "pid": os.getpid(),
    }


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path != "/identity":
            self.send_error(404)
            return
        body = json.dumps(LOADED_IDENTITY).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *_args):
        pass


if __name__ == "__main__":
    if sys.argv[1:] == ["serve"]:
        LOADED_IDENTITY = identity()
        settings = json.loads(Path("config.json").read_text(encoding="utf-8"))
        HTTPServer(("127.0.0.1", settings["port"]), Handler).serve_forever()
