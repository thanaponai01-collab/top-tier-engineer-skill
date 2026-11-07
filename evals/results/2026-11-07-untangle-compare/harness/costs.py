"""True cost of each run: total_cost_usd is cumulative across result events, so take the max.
python costs.py -> costs.json for every run dir under runs/ and the parent's tx/runs."""
import glob
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
TX = r"<scratch>\tx\runs"
out = {}
for d in sorted(glob.glob(os.path.join(HERE, "runs", "*")) + glob.glob(os.path.join(TX, "*"))):
    s = os.path.join(d, "stream.jsonl")
    if not os.path.isfile(s):
        continue
    rs = []
    for l in open(s, encoding="utf-8"):
        try:
            e = json.loads(l)
        except ValueError:
            continue
        if e.get("type") == "result":
            rs.append(e)
    name = ("plain/" if d.startswith(TX) else "") + os.path.basename(d)
    r = {"true_cost": max((x.get("total_cost_usd") or 0) for x in rs) if rs else None,
         "results": len(rs), "turns": sum(x.get("num_turns") or 0 for x in rs),
         "subtypes": [x.get("subtype") for x in rs]}
    rj = os.path.join(d, "result.json")
    if os.path.isfile(rj):
        j = json.load(open(rj, encoding="utf-8"))
        r["harness_cost"] = j.get("cost_usd")
        g = j.get("grade2")
        if g:
            r["grade2_rc"] = g.get("rc")
    out[name] = r
json.dump(out, open(os.path.join(HERE, "costs.json"), "w"), indent=1)
for k, v in out.items():
    print(k, v)
