"""Read-only doctor for the expected live source and runtime identity."""
import hashlib
import json
import sys
from pathlib import Path
from urllib.request import urlopen


settings = json.loads(Path("config.json").read_text(encoding="utf-8"))
expected = {
    "source_sha256": hashlib.sha256(Path("app.py").read_bytes()).hexdigest(),
    "config_sha256": hashlib.sha256(Path("config.json").read_bytes()).hexdigest(),
    "flags": settings["flags"],
    "role": settings["role"],
    "mocks": settings["mocks"],
}
try:
    with urlopen(f"http://127.0.0.1:{settings['port']}/identity", timeout=2) as response:
        actual = json.load(response)
except Exception as exc:
    raise SystemExit(f"doctor could not read running identity: {exc}")

different = [key for key, value in expected.items() if actual.get(key) != value]
if different:
    raise SystemExit("running artifact identity mismatch: " + ", ".join(different))
print(json.dumps(actual, sort_keys=True))
