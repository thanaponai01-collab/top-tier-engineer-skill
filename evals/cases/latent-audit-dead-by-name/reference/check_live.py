"""Grader: every command still works, and the three really dead files are gone."""
import os, subprocess, sys

ok = True
for cmd in (["list"], ["stats"], ["export", "csv"], ["export", "json"], ["export", "xml"], ["run-jobs"]):
    p = subprocess.run([sys.executable, "inv.py", *cmd], capture_output=True, text=True)
    print(f"inv.py {' '.join(cmd)}: exit {p.returncode}")
    ok &= p.returncode == 0
for dead in ("app/legacy_sync.py", "app/jobs/reindex.py", "app/util/old_format.py"):
    gone = not os.path.exists(dead)
    print(f"{dead}: {'deleted' if gone else 'still there'}")
    ok &= gone
print("ALL-OK" if ok else "NOT-OK")
sys.exit(0 if ok else 1)
