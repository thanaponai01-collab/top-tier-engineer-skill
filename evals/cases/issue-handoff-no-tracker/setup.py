import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
from history import build, FINAL

build(sys.argv[1], [
    {"message": "Tax audit moves", "date": "2026-10-06T16:00:00",
     "files": {"AUDIT.md": FINAL, "README.md": FINAL}},
])
