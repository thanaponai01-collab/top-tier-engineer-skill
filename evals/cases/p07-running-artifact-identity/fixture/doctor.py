"""Known weak doctor: a healthy HTTP response is treated as the expected service."""
import json
from pathlib import Path
from urllib.request import urlopen

settings = json.loads(Path("config.json").read_text(encoding="utf-8"))
with urlopen(f"http://127.0.0.1:{settings['port']}/identity", timeout=2) as response:
    identity = json.load(response)
assert identity.get("pid", 0) > 0, "service is not responsive"
print(json.dumps(identity, sort_keys=True))
