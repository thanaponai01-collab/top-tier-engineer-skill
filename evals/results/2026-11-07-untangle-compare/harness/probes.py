"""Per probe run: calls before first touching the real fix file, calls before editing it,
whether .untangle notes were read by a tool call, edited files, cost, grade."""
import glob
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
TX = r"<scratch>\tx\runs"
FIX = {"D1": "nativeCut.js", "D3": "sync_plan.py", "D4": "split.py"}
rows = []
for d in sorted(glob.glob(os.path.join(HERE, "runs", "*-D*")) + glob.glob(os.path.join(TX, "*-D*"))):
    if d.endswith(("graded", "graded2")) or not os.path.isfile(os.path.join(d, "stream.jsonl")):
        continue
    name = os.path.basename(d)
    probe = re.search(r"D\d", name).group(0)
    arm = "plain-orig" if name.startswith("orig") else ("plain-untangled" if name.startswith("U") else
                                                       ("ours" if name.startswith("O") else "caldo"))
    calls, cost = [], 0
    for l in open(os.path.join(d, "stream.jsonl"), encoding="utf-8"):
        try:
            e = json.loads(l)
        except ValueError:
            continue
        if e.get("type") == "result":
            cost = max(cost, e.get("total_cost_usd") or 0)
        if e.get("type") == "assistant":
            for c in e["message"]["content"]:
                if c.get("type") == "tool_use":
                    calls.append((c["name"], json.dumps(c["input"])))
    fx = FIX[probe]
    first = next((i for i, (n, s) in enumerate(calls) if fx in s), None)
    edit = next((i for i, (n, s) in enumerate(calls) if fx in s and (n in ("Edit", "Write") or
                 re.search(r"write_text|sed -i|open\([^)]*'w'|\.write\(", s))), None)
    notes = any(".untangle" in s and n in ("Read", "Bash", "Grep", "PowerShell") for n, s in calls)
    j = json.load(open(os.path.join(d, "result.json"), encoding="utf-8"))
    g = (j.get("grade2") or {}).get("rc")
    rows.append(dict(run=name, arm=arm, probe=probe, ok=g == 0, cost=round(cost, 3), calls=len(calls),
                     first_fix_touch=first, first_fix_edit=edit, read_untangle_notes=notes))
json.dump(rows, open(os.path.join(HERE, "probes.json"), "w"), indent=1)
for r in rows:
    print(r)
