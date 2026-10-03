"""Evidence gate regressions, exercised through the public CLI entry point."""
import contextlib
import copy
import importlib.util
import io
import json
from pathlib import Path
import tempfile
import time
import unittest

from _helpers import ROOT

SCRIPT = Path(ROOT) / "skills/drive/scripts/run.py"
spec = importlib.util.spec_from_file_location("drive_run", SCRIPT)
drive = importlib.util.module_from_spec(spec)
spec.loader.exec_module(drive)


class RunGate(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        self.put("app.py", "VALUE = 42\n")
        self.put("check.py", "from app import VALUE\nassert VALUE == 42\nprint('value=42')\n")
        self.put("probe.py", "from pathlib import Path\nimport sys\n"
                 "sys.exit(0 if Path('remote').exists() else 3)\n")
        self.contract = {"goal": "Correct value", "target": "local", "max_attempts": 5,
                         "timeout_seconds": 2, "max_seconds": 60,
                         "criteria": [{"statement": "value is 42", "stage": "prove"}],
                         "oracle_files": ["check.py", "probe.py"],
                         "stages": [{"id": "prove", "skill": "correctness-gate",
                                     "command": ["python", "check.py"], "inputs": ["app.py", "check.py"]}],
                         "actions": []}

    def put(self, name, text):
        (self.root / name).write_text(text, encoding="utf-8")

    def call(self, *args):
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            code = drive.main(["--repo", str(self.root), *args])
        return code, out.getvalue()

    def init(self):
        self.put("contract.json", json.dumps(self.contract))
        self.assertEqual(self.call("init", str(self.root / "contract.json"))[0], 0)

    def state(self):
        return drive.read(self.root / drive.STATE)

    def action(self, authorization="User permits this action in local simulation"):
        self.contract["actions"] = [{"id": "release", "stage": "prove", "environment": "local",
                                     "authorization": authorization, "probe": ["python", "probe.py"]}]

    def test_completion_runs_real_checks_and_is_not_a_manual_tick(self):
        self.init()
        self.assertEqual(self.call("finish")[0], 1)
        self.assertEqual(self.call("status")[0], 1)
        self.assertEqual(self.call("check", "prove")[0], 0)
        self.assertEqual(self.call("status")[0], 1)
        self.assertEqual(self.call("finish")[0], 0)
        self.assertEqual(self.call("status")[0], 0)
        self.assertEqual(self.state()["proofs"]["prove"]["output"].strip(), "value=42")

    def test_wrong_result_is_red_and_cannot_close(self):
        self.put("app.py", "VALUE = 41\n")
        self.init()
        self.assertEqual(self.call("check", "prove")[0], 1)
        self.assertEqual(self.state()["proofs"], {})
        self.assertEqual(self.call("finish")[0], 1)

    def test_out_of_order_check_and_duplicate_init_are_rejected(self):
        other = copy.deepcopy(self.contract["stages"][0])
        other["id"] = "review"
        self.contract["stages"].append(other)
        self.init()
        self.assertEqual(self.call("check", "review")[0], 1)
        self.assertEqual(self.call("init", str(self.root / "contract.json"))[0], 1)

    def test_new_source_file_makes_a_completed_run_stale(self):
        self.contract["stages"][0]["inputs"] = ["."]
        self.init()
        self.call("check", "prove")
        self.assertEqual(self.call("finish")[0], 0)
        self.put("new.py", "VALUE = 99\n")
        code, output = self.call("status")
        self.assertEqual(code, 1)
        self.assertIn("stale", output)

    def test_deleted_input_and_changed_oracle_cannot_pass(self):
        self.init()
        self.call("check", "prove")
        self.call("finish")
        (self.root / "app.py").unlink()
        self.assertEqual(self.call("status")[0], 1)
        self.put("check.py", "print('green without checking')\n")
        self.assertIn("oracle changed", self.call("status")[1])
        # Oracle damage must not trap an agent in the session.
        self.assertEqual(self.call("stop", "failed", "--reason", "oracle damaged",
                                   "--next", "owner reviews the criterion")[0], 0)

    def test_contract_edit_does_not_change_the_frozen_bar(self):
        self.init()
        state = self.state()
        state["contract"]["stages"][0]["command"] = ["python", "-c", "pass"]
        drive.save(self.root, state)
        self.assertIn("contract changed", self.call("check", "prove")[1])

    def test_restart_reconciles_applied_action_without_repeating(self):
        self.action()
        self.init()
        self.assertEqual(self.call("begin", "release")[0], 0)
        self.put("remote", "applied")  # Tool succeeds, agent dies before recording outcome.
        self.assertIn("unresolved", self.call("check", "prove")[1])
        self.assertEqual(self.call("begin", "release")[0], 1)
        self.assertEqual(self.call("reconcile", "release")[0], 0)
        self.assertEqual(self.state()["journal"]["release"]["result"], "applied")
        self.assertEqual(self.call("begin", "release")[0], 1)
        self.assertEqual(self.call("check", "prove")[0], 0)
        self.assertEqual(self.call("finish")[0], 0)

    def test_absent_action_can_retry_but_unknown_cannot(self):
        self.action()
        self.init()
        self.call("begin", "release")
        self.assertEqual(self.call("reconcile", "release")[0], 0)
        self.assertEqual(self.state()["journal"]["release"]["result"], "absent")
        self.assertEqual(self.call("begin", "release")[0], 0)
        self.assertEqual(self.state()["journal"]["release"]["attempts"], 2)

    def test_unauthorized_and_undeclared_actions_are_rejected(self):
        self.action("")
        self.init()
        self.assertIn("no user authorization", self.call("begin", "release")[1])
        self.assertEqual(self.call("begin", "charge-card")[0], 1)

    def test_missing_required_action_cannot_be_laundered_by_a_green_check(self):
        self.action()
        self.contract["actions"][0]["required"] = True
        self.init()
        self.call("check", "prove")
        self.assertIn("required action not applied", self.call("finish")[1])

    def test_probe_error_keeps_unknown(self):
        self.put("probe.py", "raise RuntimeError('provider unavailable')\n")
        self.action()
        self.init()
        self.call("begin", "release")
        self.assertEqual(self.call("reconcile", "release")[0], 1)
        self.assertEqual(self.state()["journal"]["release"]["result"], "unknown")
        self.assertEqual(self.call("begin", "release")[0], 1)

    def test_failed_handoff_is_terminal_but_not_a_success(self):
        self.init()
        self.assertEqual(self.call("stop", "blocked", "--reason", "no credentials",
                                   "--next", "connect staging read access")[0], 0)
        self.assertEqual(self.call("status")[0], 1)
        self.assertEqual(self.call("check", "prove")[0], 1)
        self.assertEqual(self.call("resume")[0], 0)
        self.assertEqual(self.call("check", "prove")[0], 0)

    def test_attempt_budget_and_elapsed_budget_survive_resume(self):
        self.contract["max_attempts"] = 1
        self.put("app.py", "VALUE = 0\n")
        self.init()
        self.call("check", "prove")
        self.assertIn("attempt budget", self.call("check", "prove")[1])
        state = self.state()
        state["started_at"] = time.time() - 61
        drive.save(self.root, state)
        self.assertIn("time budget", self.call("resume")[1])
        self.assertEqual(self.call("stop", "failed", "--reason", "budget spent",
                                   "--next", "review the failure")[0], 0)

    def test_timeout_is_not_success_and_consumes_attempt(self):
        self.put("check.py", "import time\ntime.sleep(2)\n")
        self.contract["timeout_seconds"] = 1
        self.init()
        self.assertEqual(self.call("check", "prove")[0], 1)
        self.assertEqual(self.state()["history"][-1]["exit"], 124)
        self.assertEqual(self.state()["attempts"]["prove"], 1)

    def test_finish_rechecks_external_health_instead_of_cached_green(self):
        self.put("remote", "healthy")
        self.put("check.py", "from pathlib import Path\nassert Path('remote').read_text() == 'healthy'\n")
        self.init()
        self.call("check", "prove")
        self.put("remote", "unhealthy")
        self.assertEqual(self.call("finish")[0], 1)
        self.assertNotEqual(self.state()["status"], "complete")

    def test_invalid_contracts_reject_instead_of_going_green(self):
        for contract in ([], {}, dict(self.contract, max_attempts=True),
                         dict(self.contract, criteria=[]), dict(self.contract, target="production"),
                         dict(self.contract, oracle_files=[])):
            self.put("contract.json", json.dumps(contract))
            self.assertEqual(self.call("init", str(self.root / "contract.json"))[0], 1)
        self.assertFalse((self.root / "RUN.json").exists())

    def test_input_cannot_escape_repo(self):
        self.contract["stages"][0]["inputs"] = [".."]
        self.put("contract.json", json.dumps(self.contract))
        self.assertIn("inside the repo", self.call("init", str(self.root / "contract.json"))[1])

    def test_damaged_record_can_stop_without_discarding_the_unknown_journal(self):
        raw = b'{"journal": {"release": {"result": "unknown"}'
        (self.root / "RUN.json").write_bytes(raw)
        self.assertEqual(self.call("stop", "failed", "--reason", "record interrupted",
                                   "--next", "restore journal and inspect provider")[0], 0)
        state = self.state()
        self.assertEqual((self.root / state["invalid_record"]).read_bytes(), raw)
        self.assertEqual(state["status"], "failed")
        self.assertEqual(self.call("status")[0], 1)
        self.assertEqual(self.call("resume")[0], 1)


if __name__ == "__main__":
    unittest.main()
