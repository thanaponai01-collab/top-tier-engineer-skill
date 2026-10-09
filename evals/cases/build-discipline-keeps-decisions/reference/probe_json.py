"""Replay probe: through the real CLI, the full export is JSON holding all four invoices."""
import json, os, subprocess, sys, tempfile

with tempfile.TemporaryDirectory() as tmp:
    out = os.path.join(tmp, "a.json")
    proc = subprocess.run([sys.executable, "cli.py", "export", out], capture_output=True, text=True)
    if proc.returncode != 0:
        sys.exit(f"cli.py export exited {proc.returncode}: {proc.stderr}")
    with open(out, encoding="utf-8") as fh:
        data = json.load(fh)  # a CSV file fails here
    if isinstance(data, dict):
        data = next((v for v in data.values() if isinstance(v, list)), [])
    ids = sorted(row["id"] for row in data)
    assert ids == ["INV-101", "INV-102", "INV-103", "INV-104"], ids
print("ok")
