"""Wait-free ready probe: one real identity request proves the HTTP service responds."""
import json
from pathlib import Path
from urllib.request import urlopen

settings = json.loads(Path("config.json").read_text(encoding="utf-8"))
with urlopen(f"http://127.0.0.1:{settings['port']}/identity", timeout=2) as response:
    json.load(response)
