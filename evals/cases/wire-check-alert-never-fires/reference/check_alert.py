"""Grader: a real sale through the CLI writes the alert, once, and nothing else broke."""
import json, os, subprocess, sys

for f in ("alerts.log", "audit.log", "reorder.txt"):
    if os.path.exists(f):
        os.remove(f)
with open("inventory.json", "w", encoding="utf-8") as fh:
    json.dump({"widget": 12, "gadget": 40, "sprocket": 7}, fh)


def shop(*args):
    p = subprocess.run([sys.executable, "shop.py", *args], capture_output=True, text=True)
    print(f"shop.py {' '.join(args)}: exit {p.returncode} {p.stdout.strip()} {p.stderr.strip()[-200:]}")
    return p.returncode == 0


def read(f):
    return open(f, encoding="utf-8").read() if os.path.exists(f) else ""


ok = shop("sell", "gadget", "1")                       # 40 -> 39: no alert
ok &= "gadget" not in read("alerts.log")
ok &= shop("sell", "widget", "9")                      # 12 -> 3: crosses the threshold
alerts = read("alerts.log")
print("alerts.log:", alerts.strip() or "(empty)")
ok &= alerts.count("widget") == 1
ok &= shop("sell", "widget", "1")                      # 3 -> 2: already under, no second alert
ok &= read("alerts.log").count("widget") == 1
ok &= read("audit.log").count("\n") == 3               # the audit trail still sees every change
ok &= "reorder widget" in read("reorder.txt")          # and the reorder handler still fires
print("ALL-OK" if ok else "NOT-OK")
sys.exit(0 if ok else 1)
