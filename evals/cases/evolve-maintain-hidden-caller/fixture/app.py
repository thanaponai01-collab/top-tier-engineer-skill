"""Tiny router: path -> handler. `python app.py /v2/export?fmt=csv` prints the response."""
import sys
from urllib.parse import urlsplit, parse_qs

from handlers import export_v1, export_v2, health

ROUTES = {
    "/health": health.handle,
    "/v1/export": export_v1.handle,      # deprecated 2026-05, see DEPRECATIONS.md
    "/v2/export": export_v2.handle,
}


def dispatch(url):
    parts = urlsplit(url)
    handler = ROUTES.get(parts.path)
    if handler is None:
        return 404, "not found"
    return 200, handler({k: v[0] for k, v in parse_qs(parts.query).items()})


if __name__ == "__main__":
    status, body = dispatch(sys.argv[1])
    print(status)
    print(body)
