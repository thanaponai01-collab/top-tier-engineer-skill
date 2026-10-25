"""Grader replay: the report prints exactly what it printed before, and is fast at 1x and 10x.

Copied into a scratch copy of the agent's folder beside `_make_data.py` and `_expected.txt`.
Exit 0 only when the output is unchanged, the export runs inside LIMIT_1X seconds and an export
ten times bigger inside LIMIT_10X (the original takes about 1.4 s and over a minute).
"""
import os
import subprocess
import sys
import tempfile
import time

LIMIT_1X = 0.4
LIMIT_10X = 6.0

here = os.getcwd()
sys.path.insert(0, here)
import _make_data  # noqa: E402


def run(orders, timeout):
    start = time.perf_counter()
    proc = subprocess.run([sys.executable, "report.py", orders], capture_output=True, text=True,
                          timeout=timeout)
    return time.perf_counter() - start, proc


best = None
for _ in range(3):
    seconds, proc = run(os.path.join("data", "orders.csv"), 30)
    if proc.returncode:
        sys.exit(f"report failed: {proc.stderr[-400:]}")
    best = seconds if best is None else min(best, seconds)
with open("_expected.txt", encoding="utf-8") as fh:
    if proc.stdout.replace("\r\n", "\n") != fh.read().replace("\r\n", "\n"):
        sys.exit("the report's output changed")
if best > LIMIT_1X:
    sys.exit(f"1x export took {best:.2f}s (limit {LIMIT_1X}s)")

with tempfile.TemporaryDirectory() as tmp:
    _make_data.write(tmp, 10)
    try:
        seconds, proc = run(os.path.join(tmp, "orders.csv"), LIMIT_10X * 3)
    except subprocess.TimeoutExpired:
        sys.exit("10x export timed out")
    if proc.returncode:
        sys.exit(f"10x report failed: {proc.stderr[-400:]}")
    if seconds > LIMIT_10X:
        sys.exit(f"10x export took {seconds:.2f}s (limit {LIMIT_10X}s)")
print(f"ok: 1x {best:.2f}s, 10x {seconds:.2f}s")
