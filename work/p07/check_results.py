"""Replay-safe gate for the clean paired P07 evaluation."""
import json
import sys
from pathlib import Path

case = "p07-running-artifact-identity"
root = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("evals/results/p07-run2")
summary = json.loads((root / "summary.json").read_text(encoding="utf-8"))
rows = [row for row in summary if row.get("case") == case]
without_runs = [row for row in rows if row.get("arm") == "without"]
if len(without_runs) != 1 or not without_runs[0].get("passed"):
    raise SystemExit("P07 clean comparison needs one passing no-skill baseline")
baseline_prompt = (root / case / "without-1" / "prompt.md").read_text(encoding="utf-8").lower()
if "head" in baseline_prompt:
    raise SystemExit("P07 clean baseline prompt leaked the planted revision token")

passed_with = []
for run_dir in sorted((root / case).glob("with-*")):
    result_path, prompt_path = run_dir / "result.json", run_dir / "prompt.md"
    if not result_path.is_file() or not prompt_path.is_file():
        continue
    result = json.loads(result_path.read_text(encoding="utf-8"))
    prompt = prompt_path.read_text(encoding="utf-8").lower()
    if "head" in prompt:
        raise SystemExit(f"P07 clean skill prompt leaked the planted revision token: {run_dir.name}")
    if not (result.get("passed") and result.get("report_passed") and result.get("actions_passed")):
        continue
    checks = result.get("action_checks", [])
    if not any("independent replay" in check.get("check", "").lower() and check.get("ok") for check in checks):
        continue
    if result.get("used_skill") and "verify-loop" in result.get("skills_loaded", []):
        passed_with.append(run_dir.name)
if not passed_with:
    raise SystemExit("P07 has no skill run passing the report and independent behavior gates")

history = json.loads(Path("evals/results/p07-replay/summary.json").read_text(encoding="utf-8"))
failed_history = sum(row.get("case") == case and row.get("arm") == "with" and not row.get("passed") for row in history)
if failed_history < 2:
    raise SystemExit("P07 failed/inconclusive earlier skill attempts were not preserved")
print(f"P07 isolated comparison: clean baseline passed; skill run(s) {', '.join(passed_with)} passed meaning and action gates; {failed_history} earlier failed skill attempts remain retained.")
