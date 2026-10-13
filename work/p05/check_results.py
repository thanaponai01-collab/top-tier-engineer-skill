#!/usr/bin/env python3
"""Check retained P05 baseline and final behavioral evidence."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CASES = {"arch-design-competing-candidates", "arch-design-routine"}


def load(path):
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def index(rows):
    out = {}
    for row in rows:
        key = (row["case"], row["arm"])
        if key in out:
            raise AssertionError(f"duplicate run: {key}")
        out[key] = row
    return out


baseline = index(load("evals/results/p05-baseline-v2/summary.json"))
final = index(load("evals/results/p05-final/summary.json"))
expected_baseline = {(case, arm) for case in CASES for arm in ("without", "with")}
expected_final = {(case, "with") for case in CASES}
assert set(baseline) == expected_baseline, f"baseline coverage: {set(baseline)}"
assert set(final) == expected_final, f"final coverage: {set(final)}"

models = set()
for row in baseline.values():
    models.update(row.get("models_used") or [])
for case in CASES:
    row = final[(case, "with")]
    assert row["passed"], f"final {case} did not pass"
    assert not row.get("errored") and not row.get("timed_out"), f"final {case} runner error"
    assert "arch-design" in row.get("skills_loaded", []), f"{case} did not load arch-design"
    assert row.get("action_checks") and all(c["ok"] for c in row["action_checks"]), f"{case} action failure"
    assert set(row.get("models_used") or []) == models, f"model differs for {case}"
    assert row.get("seconds", 0) < 1500, f"{case} exceeded the 25-minute cap"

trace = ROOT / "evals/results/p05-final/arch-design-competing-candidates/with-1/actions.txt"
assert "competing-designs.md" in trace.read_text(encoding="utf-8"), "consequential run skipped the procedure reference"

print("P05 retained live results: baseline 4 arms; final consequential 5/5 and routine 2/2 pass; same model; reference opened.")
