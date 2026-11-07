"""Reconstruct an untangle run from stream.jsonl.

python trace.py <run_dir> [--full]
Prints: tool timeline (main vs subagent), reads, git-history commands, test commands, edits,
token weight by phase (before first edit / editing / after last edit).
"""
import json
import os
import re
import sys
from collections import Counter

run = sys.argv[1]
full = "--full" in sys.argv
ev = [json.loads(l) for l in open(os.path.join(run, "stream.jsonl"), encoding="utf-8") if l.strip()]
calls = []   # (idx, who, name, brief, tokens_of_message)
seen_msg = set()
for e in ev:
    if e.get("type") != "assistant":
        continue
    m = e["message"]
    u = m.get("usage") or {}
    tok = (u.get("input_tokens", 0) + u.get("cache_read_input_tokens", 0)
           + u.get("cache_creation_input_tokens", 0))
    out = u.get("output_tokens", 0)
    who = "sub" if e.get("parent_tool_use_id") else "main"
    first = m.get("id") not in seen_msg
    seen_msg.add(m.get("id"))
    for c in m.get("content", []):
        if c.get("type") != "tool_use":
            continue
        i = c.get("input", {})
        n = c["name"]
        if n in ("Read",):
            b = i.get("file_path", "") + (f" @{i.get('offset')}" if i.get("offset") else "")
        elif n in ("Bash", "PowerShell"):
            b = i.get("command", "")
        elif n in ("Edit", "Write", "NotebookEdit"):
            b = i.get("file_path", "")
        elif n in ("Grep", "Glob"):
            b = f"{i.get('pattern')} in {i.get('path', '.')}"
        elif n in ("Task", "Agent"):
            b = (i.get("description", "") + " :: " + i.get("prompt", "")[:300]).replace("\n", " ")
        elif n == "Skill":
            b = json.dumps(i)
        else:
            b = json.dumps(i)[:200]
        calls.append({"who": who, "name": n, "b": b.replace("\n", " ⏎ "), "ctx": tok if first else 0,
                      "out": out if first else 0})

root = os.path.abspath(os.path.join(run, "repo")).replace("\\", "/").lower()


def rel(p):
    q = p.replace("\\", "/")
    return q[len(root) + 1:] if q.lower().startswith(root) else q


edits = [k for k, c in enumerate(calls) if c["name"] in ("Edit", "Write")
         and "/.untangle/" not in c["b"].replace("\\", "/") and "notes" not in c["b"].lower()]
fe = edits[0] if edits else len(calls)
le = edits[-1] if edits else len(calls)
ph = Counter()
for k, c in enumerate(calls):
    p = "1-before-edit" if k < fe else ("2-editing" if k <= le else "3-after-edit")
    ph[p + ":calls"] += 1
    ph[p + ":ctx"] += c["ctx"]
    ph[p + ":out"] += c["out"]

res = [e for e in ev if e.get("type") == "result"]
print("RESULT", [(r.get("subtype"), r.get("total_cost_usd"), r.get("num_turns")) for r in res])
print("calls", len(calls), Counter((c["who"], c["name"]) for c in calls).most_common())
print("phases", dict(ph))
git_cmds = [c["b"] for c in calls if c["name"] in ("Bash", "PowerShell") and re.search(r"\bgit (log|show|blame|shortlog)|untangle\.py", c["b"])]
print("\nGIT HISTORY / HELPER CMDS:", len(git_cmds))
for g in git_cmds:
    print("  ", g[:220])
tests = [c["b"] for c in calls if c["name"] in ("Bash", "PowerShell") and re.search(r"pytest|node --test|unittest", c["b"])]
print("\nTEST CMDS:", len(tests))
for t in tests:
    print("  ", t[:200])
reads = Counter(rel(c["b"].split(" @")[0]) for c in calls if c["name"] == "Read")
print("\nREADS:", sum(reads.values()), "distinct", len(reads))
for f, n in reads.most_common(40 if not full else 999):
    print(f"   {n}x {f}")
ed = Counter(rel(c["b"]) for c in calls if c["name"] in ("Edit", "Write"))
print("\nEDITS/WRITES:", sum(ed.values()))
for f, n in ed.most_common():
    print(f"   {n}x {f}")
tasks = [c for c in calls if c["name"] in ("Task", "Agent")]
print("\nSUBAGENTS:", len(tasks))
for t in tasks:
    print("  ", t["b"][:400])
if full:
    print("\nTIMELINE")
    for k, c in enumerate(calls):
        print(f"{k:4d} {c['who']:4s} {c['name']:8s} ctx={c['ctx']:>7d} {rel(c['b'])[:200]}")
