from pathlib import Path
import json
import re

ROOT = Path(__file__).resolve().parents[2]
INITIAL = ROOT / "evals/results/pstack-next"
REPLAY = ROOT / "evals/results/pstack-next-replay"
CALLER_FACT = "The billing reconciliation module is an unmapped caller of export_allowed, so the shared boundary change affects export and billing reconciliation."

def require(ok, message):
    if not ok:
        raise AssertionError(message)

def load(folder, case, arm):
    base = folder / case / f"{arm}-1"
    return json.loads((base / "result.json").read_text(encoding="utf-8")), base / "transcript.jsonl"

def trace(path):
    commands, outputs, skill_tools = [], [], []
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
                    commands.append((name, data))
                if name == "Skill":
                    skill_tools.append(data.get("skill", ""))
        if event.get("type") == "user":
            for block in (event.get("message") or {}).get("content") or []:
                if block.get("type") == "tool_result":
                    content = block.get("content", "")
                    if isinstance(content, str):
                        outputs.append(content)
                    elif isinstance(content, list):
                        outputs.extend(str(item.get("text", "")) for item in content if isinstance(item, dict))
    return commands, "\n".join(outputs), skill_tools

def command_text(commands):
    return "\n".join(name + " " + str(data.get("command") or data.get("file_path") or data) for name, data in commands).lower()

def main():
    before_control, _ = load(INITIAL, "project-context-task-trail", "without")
    before_skill, before_transcript = load(INITIAL, "project-context-task-trail", "with")
    after_control, _ = load(REPLAY, "project-context-task-trail", "without")
    after_skill, after_transcript = load(REPLAY, "project-context-task-trail", "with")

    for name, result in (("before control", before_control), ("before skill", before_skill), ("after control", after_control), ("after skill", after_skill)):
        require(not result.get("errored") and not result.get("timed_out") and not result.get("leaked"), f"context {name} errored, timed out, or leaked")
        require(result.get("actions_passed") is True, f"context {name} violated action scope")
    require(before_control.get("found") == 4 and before_control.get("missed") == [CALLER_FACT] and before_control.get("tripped") == [], "initial control did not isolate the shared-caller miss")
    before_commands, before_outputs, _ = trace(before_transcript)
    before_cmds = command_text(before_commands)
    require("find brief evidence src work -type f" in before_cmds, "initial skill arm did not retain the broad-area loading baseline")
    require("def batch_allowed" in before_outputs and "This record covers a separate subsystem with no export dependency." in before_outputs, "initial skill arm did not expose both caller and unrelated-area content in its broad sweep")
    require(before_skill.get("report_passed") is True, "initial skill arm did not find the report facts")
    require(after_control.get("found") == 4 and after_control.get("missed") == [CALLER_FACT] and after_control.get("tripped") == [], "post-change control miss changed beyond the planted caller")
    after_commands, after_outputs, after_skills = trace(after_transcript)
    after_cmds = command_text(after_commands)
    require(after_skill.get("passed") is True and after_skill.get("found") == 5 and after_skill.get("timed_out") is False, "post-change skill arm missed a fact or failed its checks")
    require("project-context" in after_skill.get("skills_loaded", []) or any("project-context" in s for s in after_skills), "post-change arm did not load project-context")
    require("reconcile.py" in after_cmds and "def batch_allowed" in after_outputs and "return export_allowed(rows)" in after_outputs, "post-change action/output evidence does not show the caller source was opened")
    require("This record covers a separate subsystem with no export dependency." not in after_outputs, "post-change arm read unrelated area content")
    print(f"Context: control {after_control['found']}/{after_control['total']} with only the planted caller miss; skill {after_skill['found']}/{after_skill['total']} and the caller source was returned by a tool read.")

    update_results = {}
    for arm in ("without", "with"):
        result, transcript = load(REPLAY, "project-update-preserves-intent", arm)
        commands, outputs, skills = trace(transcript)
        cmd_text = command_text(commands)
        require(result.get("passed") is True and not result.get("timed_out") and not result.get("errored") and not result.get("leaked"), f"upkeep {arm} did not complete cleanly")
        require(not re.search(r"\bfind\s+/|get-childitem.*-recurse.*[a-z]:\\|rg\s+--files\s+[a-z]:\\", cmd_text), f"upkeep {arm} searched outside the fixture")
        end = result.get("end_output") or {}
        require(end.get("exit") == 0 and "upkeep documents unchanged" in end.get("output", "").lower(), f"upkeep {arm} second-pass byte comparison failed")
        if arm == "with":
            require("project-update" in result.get("skills_loaded", []) or any("project-update" in s for s in skills), "upkeep skill arm did not load project-update")
            capture = cmd_text.find("upkeep_probe.py capture")
            require(capture >= 0, "upkeep skill arm did not capture document bytes")
            tail = cmd_text[capture:]
            require(re.search(r"tools/context\.py[^\n]*index --files", tail) and re.search(r"tools/context\.py[^\n]*check --files", tail), "upkeep skill arm did not run both local index/check commands after capture")
        update_results[arm] = result
        print(f"Upkeep {arm}: {result['found']}/{result['total']}, ${result.get('cost_usd') or 0:.4f}, {result.get('seconds')}s; second pass unchanged.")
    require(update_results["with"]["action_checks"] and all(c.get("ok") for c in update_results["with"]["action_checks"]), "with-skill upkeep action or document checks failed")
    print("PStack Next behavior: targeted retrieval gap closed in the one replay; repeated upkeep passed once per arm. Reliability and cost savings remain unmeasured.")

if __name__ == "__main__":
    main()

