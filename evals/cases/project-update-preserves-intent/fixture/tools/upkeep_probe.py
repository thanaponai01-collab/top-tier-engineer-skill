import hashlib
import json
import os
from pathlib import Path
import sys
import tempfile

ROOT = Path.cwd()
DOCS = [ROOT / "BRIEF.md", ROOT / "BUILD.md"] + sorted((ROOT / "work").rglob("*.md"))
STATE = Path(tempfile.gettempdir()) / ("pstack-upkeep-" + hashlib.sha256(str(ROOT.resolve()).encode()).hexdigest()[:16] + ".json")

def current():
    return {p.relative_to(ROOT).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest() for p in DOCS if p.is_file()}

if len(sys.argv) != 2 or sys.argv[1] not in {"capture", "compare"}:
    raise SystemExit("usage: python tools/upkeep_probe.py capture|compare")
if sys.argv[1] == "capture":
    STATE.write_text(json.dumps(current(), indent=2), encoding="utf-8")
    print(f"captured {len(current())} context documents")
else:
    if not STATE.is_file():
        raise SystemExit("first-pass snapshot missing")
    before = json.loads(STATE.read_text(encoding="utf-8"))
    after = current()
    if before != after:
        changed = sorted(set(before) ^ set(after) | {p for p in before.keys() & after.keys() if before[p] != after[p]})
        print("second-pass document changes: " + ", ".join(changed))
        raise SystemExit(1)
    print("upkeep documents unchanged")
