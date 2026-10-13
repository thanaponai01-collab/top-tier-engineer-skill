import json
from pathlib import Path

root = Path(__file__).resolve().parents[2]
summary = root / "evals/results/2026-10-13-1804/summary.json"
runs = json.loads(summary.read_text(encoding="utf-8"))
selected = [r for r in runs if r.get("case") == "p08-standalone-small-task"]
by_arm = {arm: [r for r in selected if r.get("arm") == arm] for arm in ("without", "with")}
if any(len(by_arm[arm]) != 1 for arm in by_arm):
    raise SystemExit("P08 baseline must retain exactly one run in each arm")
for arm, records in by_arm.items():
    record = records[0]
    if not record.get("passed") or not record.get("actions_passed"):
        raise SystemExit(f"P08 baseline {arm} run did not pass report and action gates")
print("P08 baseline: without 1/1 and with 1/1 passed; direct handling already works, so no improvement is claimed.")
