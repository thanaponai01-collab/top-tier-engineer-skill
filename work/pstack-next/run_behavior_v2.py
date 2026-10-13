from pathlib import Path
import json
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "evals/results/pstack-next-replay"
CASES = ("project-context-task-trail", "project-update-preserves-intent")
ARMS = ("with", "without")

def require(ok, message):
    if not ok:
        raise AssertionError(message)

def load(case, arm):
    folder = OUT / case / f"{arm}-1"
    result_path, actions_path = folder / "result.json", folder / "actions.txt"
    if not result_path.is_file() or not actions_path.is_file():
        raise AssertionError(f"missing retained result or actions in {folder}")
    return json.loads(result_path.read_text(encoding="utf-8")), actions_path.read_text(encoding="utf-8").lower()

def run_trial_if_needed():
    expected = [OUT / case / f"{arm}-1/result.json" for case in CASES for arm in ARMS]
    if all(path.is_file() for path in expected):
        return
    command = [sys.executable, "evals/run.py", "--cases", *CASES, "--repeats", "1", "--arms", "with,without", "--jobs", "1", "--budget-usd", "1", "--timeout", "360", "--no-scorecard", "--out", str(OUT.relative_to(ROOT))]
    run = subprocess.run(command, cwd=ROOT, text=True, capture_output=True, timeout=2100)
    print(run.stdout, end="")
    print(run.stderr, end="", file=sys.stderr)
    if run.returncode:
        raise SystemExit(run.returncode)

def main():
    run_trial_if_needed()
    for arm in ARMS:
        result, actions = load("project-context-task-trail", arm)
        require(not result.get("errored") and not result.get("leaked") and not result.get("timed_out"), f"context {arm} errored, leaked, or timed out")
        require(result.get("actions_passed") is True, f"context {arm} action scope failed")
        if arm == "with":
            require(result.get("passed") is True and result.get("found") == 5, "skill arm did not recover every planted fact")
            require("project-context" in result.get("skills_loaded", []), "skill arm did not load project-context")
            require("reconcile.py" in actions and re.search(r"(?:read:|get-content|type\\s+|cat\\s+).*reconcile\.py", actions), "skill arm did not open the unmapped shared caller source")
            require(not re.search(r"(?:read:|get-content|type\\s+|cat\\s+).*work[\\/]unrelated[\\/].*\.md", actions), "skill arm opened an unrelated area record")
        else:
            require(result.get("found") == 4 and result.get("missed") == ["The billing reconciliation module is an unmapped caller of export_allowed, so the shared boundary change affects export and billing reconciliation."], "control did not isolate the planted shared-caller miss")
            require(not result.get("tripped") and not result.get("changes", {}).get("changed") and not result.get("changes", {}).get("added"), "control violated the report-only task")
        print(f"PStack context {arm}: {result.get('found')}/{result.get('total')}, ${result.get('cost_usd') or 0:.4f}, {result.get('seconds')}s")

    for arm in ARMS:
        result, actions = load("project-update-preserves-intent", arm)
        require(not result.get("errored") and not result.get("leaked") and not result.get("timed_out"), f"upkeep {arm} errored, leaked, or timed out")
        require(result.get("passed") is True, f"upkeep {arm} failed: {result.get('missed')} {result.get('action_checks')}")
        require(not re.search(r"find\s+/|get-childitem.*-recurse.*[a-z]:\\|rg\s+--files\s+[a-z]:\\", actions), f"upkeep {arm} searched outside the fixture")
        end = result.get("end_output") or {}
        require(end.get("exit") == 0 and "upkeep documents unchanged" in end.get("output", "").lower(), f"upkeep {arm} second-pass document snapshot failed")
        if arm == "with":
            require("project-update" in result.get("skills_loaded", []), "skill arm did not load project-update")
            capture = actions.find("upkeep_probe.py capture")
            require(capture >= 0, "skill arm did not capture first-pass document bytes")
            tail = actions[capture:]
            require("tools/context.py" in tail and "index" in tail and "check" in tail, "skill arm did not repeat both local context index and check after capture")
        print(f"PStack upkeep {arm}: {result.get('found')}/{result.get('total')}, ${result.get('cost_usd') or 0:.4f}, {result.get('seconds')}s")
    print("PStack Next replay: targeted baseline miss preserved; skill arm read unmapped caller; repeated upkeep and unchanged-doc proof observed.")

if __name__ == "__main__":
    main()
