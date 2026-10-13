from pathlib import Path
import json
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
INITIAL = ROOT / "evals/results/pstack-next"
CONTEXT_REPLAY = ROOT / "evals/results/pstack-next-replay"
UPDATE_REPLAY = ROOT / "evals/results/pstack-next-replay-v2"
UPDATE_CASE = "project-update-preserves-intent"
CONTEXT_CASE = "project-context-task-trail"
CALLER_FACT = "The billing reconciliation module is an unmapped caller of export_allowed, so the shared boundary change affects export and billing reconciliation."

def require(ok, message):
    if not ok:
        raise AssertionError(message)

def load(folder, case, arm):
    base = folder / case / f"{arm}-1"
    return json.loads((base / "result.json").read_text(encoding="utf-8")), base / "transcript.jsonl"

def trace(path):
    calls, outputs, skills = [], [], []
    for line in path.read_text(encoding="utf-8").splitlines():
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue
        if event.get("type") == "assistant":
            for block in (event.get("message") or {}).get("content") or []:
                if block.get("type") != "tool_use":
                    continue
                name, data = block.get("name", ""), block.get("input") or {}
                if name in {"Bash", "Read", "Glob", "Grep", "Skill"}:
                    calls.append((name, data))
                if name == "Skill":
                    skills.append(data.get("skill", ""))
        elif event.get("type") == "user":
            for block in (event.get("message") or {}).get("content") or []:
                if block.get("type") == "tool_result":
                    content = block.get("content", "")
                    if isinstance(content, str):
                        outputs.append(content)
                    elif isinstance(content, list):
                        outputs.extend(str(item.get("text", "")) for item in content if isinstance(item, dict))
    return calls, "\n".join(outputs), skills

def commands(calls):
    return "\n".join(name + " " + str(data.get("command") or data.get("file_path") or data) for name, data in calls).lower()

def run_upkeep_if_needed():
    expected = [UPDATE_REPLAY / UPDATE_CASE / f"{arm}-1/result.json" for arm in ("with", "without")]
    if all(path.is_file() for path in expected):
        return
    command = [sys.executable, "evals/run.py", "--cases", UPDATE_CASE, "--repeats", "1", "--arms", "with,without", "--jobs", "1", "--budget-usd", "1", "--timeout", "360", "--no-scorecard", "--out", str(UPDATE_REPLAY.relative_to(ROOT))]
    run = subprocess.run(command, cwd=ROOT, text=True, capture_output=True, timeout=1100)
    print(run.stdout, end="")
    print(run.stderr, end="", file=sys.stderr)
    if run.returncode:
        raise SystemExit(run.returncode)

def main():
    initial_control, _ = load(INITIAL, CONTEXT_CASE, "without")
    initial_skill, initial_transcript = load(INITIAL, CONTEXT_CASE, "with")
    current_control, _ = load(CONTEXT_REPLAY, CONTEXT_CASE, "without")
    current_skill, current_transcript = load(CONTEXT_REPLAY, CONTEXT_CASE, "with")
    for label, result in (("initial control", initial_control), ("initial skill", initial_skill), ("replay control", current_control), ("replay skill", current_skill)):
        require(not result.get("errored") and not result.get("timed_out") and not result.get("leaked"), f"context {label} errored, timed out, or leaked")
        require(result.get("actions_passed") is True, f"context {label} violated scope checks")
    require(initial_control.get("found") == 4 and initial_control.get("missed") == [CALLER_FACT] and not initial_control.get("tripped"), "initial control did not isolate the planted caller miss")
    initial_calls, initial_outputs, _ = trace(initial_transcript)
    initial_commands = commands(initial_calls)
    require("find brief evidence src work -type f" in initial_commands and "This record covers a separate subsystem with no export dependency." in initial_outputs, "initial with-skill replay does not demonstrate the broad-area loading baseline")
    require(initial_skill.get("report_passed") is True, "initial skill arm did not recover report facts")
    require(current_control.get("found") == 4 and current_control.get("missed") == [CALLER_FACT] and not current_control.get("tripped"), "replay control miss differs from the targeted baseline miss")
    calls, outputs, loaded = trace(current_transcript)
    cmd = commands(calls)
    require(current_skill.get("passed") is True and current_skill.get("found") == 5, "project-context replay did not pass all facts")
    require("project-context" in current_skill.get("skills_loaded", []) or any("project-context" in s for s in loaded), "project-context replay did not load the skill")
    require("reconcile.py" in cmd and "def batch_allowed" in outputs and "return export_allowed(rows)" in outputs, "project-context replay lacks a successful direct read of the shared caller")
    require("This record covers a separate subsystem with no export dependency." not in outputs, "project-context replay read unrelated area content")
    print(f"Context: initial skill broad sweep included unrelated content; replay skill opened the caller selectively ({current_skill['found']}/{current_skill['total']}); control retained only the planted miss.")

    run_upkeep_if_needed()
    for arm in ("without", "with"):
        result, transcript = load(UPDATE_REPLAY, UPDATE_CASE, arm)
        calls, outputs, loaded = trace(transcript)
        cmd = commands(calls)
        require(result.get("passed") is True and not result.get("timed_out") and not result.get("errored") and not result.get("leaked"), f"upkeep {arm} did not complete cleanly")
        require(not re.search(r"\bfind\s+/|get-childitem.*-recurse.*[a-z]:\\|rg\s+--files\s+[a-z]:\\|[a-z]:[\\/]+users[\\/]+[^\\/]+[\\/]+\.claude[\\/]+projects", cmd), f"upkeep {arm} searched outside the fixture")
        end = result.get("end_output") or {}
        require(end.get("exit") == 0 and "upkeep documents unchanged" in end.get("output", "").lower(), f"upkeep {arm} second-pass document snapshot failed")
        capture = cmd.find("upkeep_probe.py capture")
        require(capture >= 0, f"upkeep {arm} did not capture the first-pass document bytes")
        tail = cmd[capture:]
        require(re.search(r"tools/context\.py[^\n]*index --files", tail) and re.search(r"tools/context\.py[^\n]*check --files", tail), f"upkeep {arm} did not repeat local index/check after capture")
        if arm == "with":
            require("project-update" in result.get("skills_loaded", []) or any("project-update" in s for s in loaded), "project-update replay did not load the skill")
        print(f"Upkeep {arm}: {result['found']}/{result['total']}, ${result.get('cost_usd') or 0:.4f}, {result.get('seconds')}s; repeated index/check left Markdown unchanged.")
    print("PStack Next behavior: bounded fresh-reader and repeated-upkeep trials passed once per arm; reliability and savings remain unmeasured.")

if __name__ == "__main__":
    main()
