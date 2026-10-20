#!/usr/bin/env python3
"""Summarize one eval batch against a predeclared verify-loop trust bar.

Reads saved outcomes; does not run agents or infer a release verdict from prose.
Guardrail failures are grader traps, a proxy rather than a measured false-green rate.
"""
import argparse
import hashlib
import json
from pathlib import Path


def summarize(rows, policy, arm="with"):
    selected = [r for r in rows if r.get("skill") == policy["skill"] and r.get("arm") == arm]
    groups = {}
    for split in ("development", "held_out"):
        cases = policy[split]
        runs = [r for r in selected if r.get("case") in cases]
        valid = [r for r in runs if not any(r.get(k) for k in ("errored", "timed_out", "leaked"))]
        counts = {c: sum(r.get("case") == c for r in valid) for c in cases}
        passed_counts = {c: sum(r.get("case") == c and r.get("passed") is True for r in valid)
                         for c in cases}
        guarded = [r for r in valid if r["case"] in policy["guardrail_cases"]]
        # Missing trap fields are unknown evidence, never an observed zero.
        observed = [r for r in guarded if isinstance(r.get("tripped"), list)]
        failures = sum(bool(r["tripped"]) for r in observed)
        rate = sum(r.get("passed") is True for r in valid) / len(valid) if valid else None
        guard_rate = failures / len(observed) if observed else None
        complete = all(n >= policy["minimum_repeats"] for n in counts.values())
        met = (complete and len(valid) == len(runs) and len(observed) == len(guarded)
               and rate is not None and rate >= policy["minimum_task_pass_rate"]
               and (not guarded or guard_rate <= policy["maximum_guardrail_failure_rate"]))
        costs = [r["cost_usd"] for r in runs if isinstance(r.get("cost_usd"), (int, float))]
        times = [r["seconds"] for r in runs if isinstance(r.get("seconds"), (int, float))]
        groups[split] = {
            "bar_met": met, "valid_runs": len(valid), "invalid_runs": len(runs) - len(valid),
            "runs_per_case": counts, "task_pass_rate": rate,
            "passes_per_case": passed_counts,
            "guardrail_observations": len(observed), "guardrail_failures": failures,
            "guardrail_failure_rate": guard_rate,
            "cost_usd": sum(costs) if len(costs) == len(runs) and runs else None,
            "mean_seconds": sum(times) / len(times) if len(times) == len(runs) and runs else None,
        }
    return {"bar_met": all(g["bar_met"] for g in groups.values()), "arm": arm,
            "models": sorted({r.get("model", "unknown") for r in selected}), "splits": groups}


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("summary", type=Path, help="one batch's summary.json; do not pool tuned batches")
    ap.add_argument("--policy", type=Path, default=Path(__file__).with_name("verify-trust.json"))
    ap.add_argument("--arm", choices=("with", "without"), default="with")
    ap.add_argument("--output", type=Path, help="retain the JSON scorecard")
    args = ap.parse_args()
    result = summarize(json.loads(args.summary.read_text(encoding="utf-8")),
                       json.loads(args.policy.read_text(encoding="utf-8")), args.arm)
    result["source"] = str(args.summary)
    result["source_sha256"] = hashlib.sha256(args.summary.read_bytes()).hexdigest()
    result["policy_sha256"] = hashlib.sha256(args.policy.read_bytes()).hexdigest()
    rendered = json.dumps(result, indent=2)
    if args.output:
        if args.output.resolve() in (args.summary.resolve(), args.policy.resolve()):
            ap.error("output must not overwrite the summary or policy")
        args.output.write_text(rendered + "\n", encoding="utf-8")
    print(rendered)
    return 0 if result["bar_met"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
