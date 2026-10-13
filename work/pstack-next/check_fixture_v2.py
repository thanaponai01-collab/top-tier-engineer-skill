from pathlib import Path
import hashlib
import json

root = Path(__file__).resolve().parents[2]
context = root / "evals/cases/project-context-task-trail"
update = root / "evals/cases/project-update-preserves-intent"
files = [p for p in (context / "fixture").rglob("*") if p.is_file() and ".git" not in p.parts]
assert len(files) >= 24, f"larger context fixture has only {len(files)} files"
caller = context / "fixture/src/billing/reconcile.py"
assert caller.is_file(), "unmapped shared caller missing"
features = (context / "fixture/FEATURES.md").read_text(encoding="utf-8")
assert "src/billing/reconcile.py" not in features, "shared caller must be outside the starting feature map"
assert len(list((context / "fixture/work/unrelated").glob("*.md"))) >= 8, "unrelated context records missing"
ctx_expect = json.loads((context / "expect.json").read_text(encoding="utf-8"))
assert any(row["id"] == "shared-caller" for row in ctx_expect["planted"])
assert any(row["id"] == "unrelated-sweep" for row in ctx_expect["traps"])
fixture_helper = update / "fixture/tools/context.py"
actual_helper = root / "skills/project-context/scripts/context.py"
assert fixture_helper.is_file(), "local context helper missing"
assert hashlib.sha256(fixture_helper.read_bytes()).digest() == hashlib.sha256(actual_helper.read_bytes()).digest(), "fixture helper differs from the real project-context helper"
up_expect = json.loads((update / "expect.json").read_text(encoding="utf-8"))
assert any("find\\s+/" in pattern for pattern in up_expect["actions"]["must_not_run_any"]), "host-wide search is not rejected"
assert any(".claude" in pattern and "projects" in pattern for pattern in up_expect["actions"]["must_not_run_any"]), "global memory access is not rejected"
assert (update / "fixture/tools/upkeep_probe.py").is_file(), "second-pass byte probe missing"
prompt = (update / "prompt.md").read_text(encoding="utf-8").lower()
assert "tools/context.py" in prompt and "use only files inside the fixture" in prompt
plain_prompt = (update / "prompt-plain.md").read_text(encoding="utf-8").lower()
assert "tools/context.py" in plain_prompt and "use only files inside the fixture" in plain_prompt
assert prompt == plain_prompt, "with/without task prompts differ"
print(f"PStack Next replay fixture: {len(files)} context files, real unmapped caller/helper, {len(list((context / 'fixture/work/unrelated').glob('*.md')))} unrelated areas, bounded repeated upkeep.")




