"""Replay probe: the finished export writes JSON and `--month` keeps only that month."""
import json, os, subprocess, sys, tempfile


def ids(path):
    with open(path, encoding="utf-8") as fh:
        data = json.load(fh)  # a CSV file fails here
    if isinstance(data, dict):
        data = next((v for v in data.values() if isinstance(v, list)), [])
    return sorted(row["id"] for row in data)


with tempfile.TemporaryDirectory() as tmp:
    month, every = os.path.join(tmp, "m.json"), os.path.join(tmp, "a.json")
    for args in ([every], [month, "--month", "2026-09"]):
        proc = subprocess.run([sys.executable, "cli.py", "export", *args], capture_output=True, text=True)
        if proc.returncode != 0:
            sys.exit(f"cli.py export {' '.join(args)} exited {proc.returncode}: {proc.stderr}")
    assert ids(every) == ["INV-101", "INV-102", "INV-103", "INV-104"], ids(every)
    assert ids(month) == ["INV-103", "INV-104"], ids(month)
print("ok")
