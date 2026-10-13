from pathlib import Path
import json

root = Path(__file__).resolve().parents[2]
context = root / "evals/cases/project-context-task-trail"
update = root / "evals/cases/project-update-preserves-intent"

context_files = [p for p in (context / "fixture").rglob("*") if p.is_file() and ".git" not in p.parts]
assert len(context_files) >= 24, f"larger context fixture has only {len(context_files)} files"
assert (context / "fixture/src/billing/reconcile.py").is_file(), "unmapped shared caller is missing"
features = (context / "fixture/FEATURES.md").read_text(encoding="utf-8")
assert "src/billing/reconcile.py" not in features, "shared caller should be outside the initial map"
assert len(list((context / "fixture/work/unrelated").glob("*.md"))) >= 8, "unrelated areas are too small"
expect = json.loads((context / "expect.json").read_text(encoding="utf-8"))
assert any(x["id"] == "shared-caller" for x in expect["planted"]), "shared caller is not independently graded"
assert any(x["id"] == "unrelated-sweep" for x in expect["traps"]), "unrelated loading is not graded"
update_fixture = update / "fixture"
probe = update_fixture / "tools/upkeep_probe.py"
assert probe.is_file(), "second-pass snapshot probe is missing"
update_prompt = (update / "prompt.md").read_text(encoding="utf-8").lower()
assert "capture" in update_prompt and "repeat" in update_prompt, "prompt lacks an observed repeat pass"
update_expect = json.loads((update / "expect.json").read_text(encoding="utf-8"))
assert update_expect.get("actions", {}).get("end_state", {}).get("cmd") == "python tools/upkeep_probe.py compare", "unchanged second-pass end-state is not gated"
print(f"PStack Next fixtures: {len(context_files)} context files, 8+ unrelated areas, an unmapped shared caller, and a second-pass byte snapshot probe.")
