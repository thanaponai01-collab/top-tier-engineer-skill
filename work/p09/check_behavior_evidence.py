import json
from pathlib import Path


root = Path(__file__).resolve().parents[2]
folder = root / "evals/results/p09-verified"
summary = json.loads((folder / "summary.json").read_text(encoding="utf-8"))
assert len(summary) == 2, "expected one retained result per arm"
by_arm = {item["arm"]: item for item in summary}
assert set(by_arm) == {"with", "without"}, "expected both arms"
control = by_arm["without"]
with_skill = by_arm["with"]
assert control["found"] == 7 and control["total"] == 8 and not control["passed"], "control must retain the targeted miss"
assert "MISSED  unowned-shared-storage" in control["judge_text"], "control missed a different result"
assert with_skill["found"] == with_skill["total"] == 8 and with_skill["passed"], "Drive arm must pass all findings"
assert with_skill["skills_loaded"] == ["drive"], "Drive was not read"
assert with_skill["dispatch_count"] == control["dispatch_count"] == 0, "this trial did not test dispatch"
for arm, item in by_arm.items():
    assert item["actions_passed"], f"{arm} failed read-only or no-forge-action checks"
    assert not item["errored"] and not item["leaked"], f"{arm} failed harness controls"
with_actions = (folder / "drive-program-delivery/with-1/actions.txt").read_text(encoding="utf-8").replace("\\", "/")
assert "references/program-delivery.md" in with_actions, "the new reference was not read"
assert by_arm["with"]["model"] == by_arm["without"]["model"], "the arms used different models"
print("P09 behavior evidence: with Drive 8/8; control 7/8 with the targeted shared-storage miss; reference read; actions stayed local.")
