import json
from pathlib import Path
import subprocess
import sys


root = Path(__file__).resolve().parents[2]
command = [
    sys.executable, "evals/run.py", "--cases", "drive-program-delivery", "--repeats", "1",
    "--arms", "without,with", "--jobs", "1", "--budget-usd", "2", "--out",
    "evals/results/p09-verified", "--keep-workdirs",
]
run = subprocess.run(command, cwd=root, text=True, capture_output=True)
print(run.stdout, end="")
print(run.stderr, end="", file=sys.stderr)
if run.returncode:
    raise SystemExit(run.returncode)

summary = json.loads((root / "evals/results/p09-verified/summary.json").read_text(encoding="utf-8"))
if len(summary) != 2 or {item.get("arm") for item in summary} != {"without", "with"}:
    raise SystemExit("behavior check rejected: expected exactly one result per arm")
for item in summary:
    arm = item["arm"]
    if not item.get("actions_passed"):
        raise SystemExit(f"behavior check rejected: {arm} failed read-only or no-forge-action checks")
    if item.get("total") != 8 or item.get("dispatch_count") != 0:
        raise SystemExit(f"behavior check rejected: unexpected rubric size for {arm}")
with_skill = next(item for item in summary if item["arm"] == "with")
without = next(item for item in summary if item["arm"] == "without")
if not with_skill.get("passed") or with_skill.get("found") != 8:
    raise SystemExit("behavior check rejected: Drive arm did not pass all 8 findings")
if with_skill.get("skills_loaded") != ["drive"]:
    raise SystemExit("behavior check rejected: the staged Drive skill was not actually read")
if without.get("passed") or without.get("found") != 7 or "MISSED  unowned-shared-storage" not in without.get("judge_text", ""):
    raise SystemExit("behavior check rejected: control arm did not retain the baseline shared-storage miss")
print("P09 behavior: Drive passed 8/8; control missed the unowned-storage finding at 7/8; action checks passed.")
