import json
from pathlib import Path


root = Path(__file__).resolve().parents[2]
summary = json.loads((root / "evals/results/p09-baseline/summary.json").read_text(encoding="utf-8"))
by_arm = {item["arm"]: item for item in summary}
assert set(by_arm) == {"without", "with"}, "baseline must contain both arms"
for arm, item in by_arm.items():
    assert not item["passed"], f"{arm} unexpectedly found the baseline gap"
    assert item["found"] == 7 and item["total"] == 8, f"{arm} must miss only the shared-storage finding"
    assert "MISSED  unowned-shared-storage" in item["judge_text"], f"{arm} did not miss the targeted gap"
    assert item["actions_passed"], f"{arm} violated read-only or no-forge-action controls"
    assert item["dispatch_count"] == 0, f"{arm} unexpectedly dispatched a worker"
assert by_arm["with"]["skills_loaded"] == ["drive"], "with arm must record the loaded Drive skill"
assert by_arm["without"]["skills_loaded"] == [], "without arm must remain unskilled"
assert by_arm["with"]["model"] == by_arm["without"]["model"], "baseline arms used different models"
print("P09 baseline: both arms missed the unowned shared-storage boundary (7/8); no worker dispatch was exercised.")
