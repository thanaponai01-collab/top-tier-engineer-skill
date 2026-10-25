"""Push stock to the old warehouse API. The warehouse moved to CSV drops in 2025."""
import json
import urllib.request

ENDPOINT = "http://warehouse.internal/api/v1/stock"


def push(items):
    req = urllib.request.Request(ENDPOINT, data=json.dumps(items).encode(),
                                 headers={"Content-Type": "application/json"})
    return urllib.request.urlopen(req, timeout=5).status
