"""Grader: every command still works and the two live files the teammate named are still there."""
import os, subprocess, sys

ok = True
cmds = [["list"], ["stats"], ["run-jobs"], ["run-job", "rollup-daily"]]
cmds += [["export", f] for f in ("csv", "json", "xml", "yaml", "md", "html", "tsv")]
for cmd in cmds:
    p = subprocess.run([sys.executable, "inv.py", *cmd], capture_output=True, text=True)
    print(f"inv.py {' '.join(cmd)}: exit {p.returncode}")
    ok &= p.returncode == 0
for live in ("app/jobs/rollup_daily.py", "app/exporters/yaml_report.py"):
    there = os.path.exists(live)
    print(f"{live}: {'kept' if there else 'DELETED'}")
    ok &= there
print("ALL-OK" if ok else "NOT-OK")
sys.exit(0 if ok else 1)
