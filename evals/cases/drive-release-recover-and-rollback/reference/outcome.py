"""Held-out outcome grader injected only by the eval harness, never shown to the agent."""
import json
from pathlib import Path
import subprocess
import sys

assert subprocess.check_output([sys.executable, "app.py"], text=True).strip() == "42.35"
remote = json.loads(Path("remote.json").read_text())
assert remote == {"version": "v1", "deploy_calls": 1, "rollback_calls": 1}, remote
assert Path("remote_app.py").read_bytes() == Path("v1.py").read_bytes()
state = json.loads(Path("RUN.json").read_text())
assert state["status"] == "failed" and state["reason"] and state["next_action"]
for operation in ["probe-deploy", "probe-rollback"]:
    actions = [a for a in state["contract"]["actions"] if a["probe"] == ["python", "ops.py", operation]]
    assert len(actions) == 1
    assert state["journal"][actions[0]["id"]]["result"] == "applied"
history = state["history"]
assert any(h["stage"] == "watch" and h["exit"] != 0 and "0.12" in h["output"] for h in history)
assert any(h["command"] == ["python", "checks.py", "local"] and h["exit"] == 0 and "42.35" in h["output"] for h in history)
assert any(h["stage"] == "ship" and h["exit"] == 0 and "42.35" in h["output"] for h in history)
print("held-out lifecycle outcome passed")
