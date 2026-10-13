from pathlib import Path
import json
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "evals/results/pstack-next"
CASES = ("project-context-task-trail", "project-update-preserves-intent")
ARMS = ("with", "without")

def require(ok, message):
    if not ok:
        raise AssertionError(message)

def load(case, arm):
    path = OUT / case / f"{arm}-1"
    result_path, action_path = path / "result.json", path / "actions.txt"
    if not result_path.is_file() or not action_path.is_file():
        raise AssertionError(f"missing retained result or actions: {path}")
    return json.loads(result_path.read_text(encoding="utf-8")), action_path.read_text(encoding="utf-8").lower()

def run_trial_if_needed():
    results = [OUT / case / f"{arm}-1/result.json" for case in CASES for arm in ARMS]
    if all(path.is_file() for path in results):
        return
    command = [sys.executable, "evals/run.py", "--cases", *CASES, "--repeats", "1", "--arms", "with,without", "--jobs", "1", "--budget-usd", "1", "--timeout", "300", "--no-scorecard", "--out", str(OUT.relative_to(ROOT))]
    run = subprocess.run(command, cwd=ROOT, text=True, capture_output=True, timeout=1800)
    print(run.stdout, end="")
    print(run.stderr, end="", file=sys.stderr)
    if run.returncode:
        raise SystemExit(run.returncode)

def main():
    run_trial_if_needed()
    for case in CASES:
        for arm in ARMS:
            result, _ = load(case, arm)
            require(result.get("passed") is True, f"{case} {arm} did not pass: missed={result.get('missed')} tripped={result.get('tripped')} actions={result.get('action_checks')}")
            require(not result.get("errored") and not result.get("leaked"), f"{case} {arm} errored or leaked answers")
            print(f"PASS {case} {arm}: {result.get('found')}/{result.get('total')}, ${result.get('cost_usd') or 0:.4f}, {result.get('seconds')}s")

    for arm in ARMS:
        result, actions = load("project-context-task-trail", arm)
        require("project-context" in result.get("skills_loaded", []) if arm == "with" else True, "with context arm did not load project-context")
        require("reconcile.py" in actions and re.search(r"(?:read:|get-content|type\\s+|cat\\s+).*reconcile\.py", actions), f"context {arm} lacks direct evidence of opening the unmapped shared caller")
        require(not re.search(r"(?:read:|get-content|type\\s+|cat\\s+).*work[\\/]unrelated[\\/].*\.md", actions), f"context {arm} opened unrelated area records")
        require("test_limits" in actions and ("unittest" in actions or "pytest" in actions), f"context {arm} lacks the current safe boundary check")

    update_result, update_actions = load("project-update-preserves-intent", "with")
    require("project-update" in update_result.get("skills_loaded", []), "with update arm did not load project-update")
    capture = update_actions.find("upkeep_probe.py capture")
    require(capture >= 0, "with update arm did not save the first-pass document state")
    after_capture = update_actions[capture:]
    require("context.py" in after_capture and "index" in after_capture and "check" in after_capture, "with update arm lacks a second context index/check pass after capture")
    end = update_result.get("end_output") or {}
    require(end.get("exit") == 0 and "upkeep documents unchanged" in end.get("output", "").lower(), "second-pass document snapshot changed or was not verified")
    print("PStack Next behavior: both cases passed in both arms; direct shared-caller read, bounded loading, second upkeep action, and unchanged document snapshot observed.")

if __name__ == "__main__":
    main()
