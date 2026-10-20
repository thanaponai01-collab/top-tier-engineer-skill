"""1.11.0: separate judge from worker. `baseline` records which VERIFY_AGENT froze each check, and
`require: independent` keeps `run --strict` red (NOT INDEPENDENT) while the agent that froze a check
is the agent whose run claims green.

Run with: python -m unittest discover tests
"""
import json, os, subprocess, sys, tempfile, unittest
from pathlib import Path

from _helpers import SCRIPTS

VERIFY = os.path.join(SCRIPTS["verify.py"], "verify.py")
RECIPE = ("require: independent\n\n## Answer\n- test: `python check.py`\n- oracle: check.py\n"
          "- fail-signal: expected 42\n- fail-proof: value 41 rejected\n")


def verify(*args, agent=None):
    env = dict(os.environ)
    env.pop("VERIFY_AGENT", None)
    if agent is not None:
        env["VERIFY_AGENT"] = agent
    p = subprocess.run([sys.executable, VERIFY, *args], capture_output=True, text=True,
                       encoding="utf-8", env=env)
    return p.returncode, p.stdout + p.stderr


def proved_repo(root, recipe=RECIPE, freezer="judge"):
    """A check seen red with its signal, then fixed and frozen by `freezer`."""
    Path(root, "check.py").write_text("assert open('value.txt').read() == '42', 'expected 42'\n")
    Path(root, "value.txt").write_text("41")
    Path(root, "VERIFY.md").write_text(recipe)
    verify("run", root, agent="worker")
    Path(root, "value.txt").write_text("42")
    code, out = verify("baseline", root, agent=freezer)
    assert code == 0, out


class Independence(unittest.TestCase):
    def test_the_agent_that_froze_the_check_cannot_claim_green(self):
        with tempfile.TemporaryDirectory() as root:
            proved_repo(root)
            code, out = verify("run", root, "--strict", agent="judge")
            self.assertEqual(code, 1, out)
            self.assertIn("NOT INDEPENDENT", out)
            self.assertEqual(verify("status", root, agent="judge")[0], 1)
            code, out = verify("run", root, "--strict", agent="worker")
            self.assertEqual(code, 0, out)
            self.assertEqual(verify("status", root, agent="worker")[0], 0)

    def test_unnamed_agents_cannot_show_independence(self):
        with tempfile.TemporaryDirectory() as root:
            proved_repo(root, freezer=None)
            code, out = verify("run", root, "--strict", agent="worker")
            self.assertEqual(code, 1, out)
            self.assertIn("NOT INDEPENDENT", out)

    def test_rebaseline_by_the_worker_keeps_the_original_freezer_of_unchanged_checks(self):
        with tempfile.TemporaryDirectory() as root:
            proved_repo(root)
            self.assertEqual(verify("baseline", root, agent="worker")[0], 0)
            self.assertEqual(verify("run", root, "--strict", agent="worker")[0], 0)

    def test_report_lists_the_gap_and_json_counts_it(self):
        with tempfile.TemporaryDirectory() as root:
            proved_repo(root)
            code, out = verify("run", root, "--strict", "--json", agent="judge")
            self.assertEqual(json.loads(out)["summary"]["not_independent"], 1)
            code, out = verify("report", root, agent="judge")
            self.assertIn("GAP  not independent: Answer", out)
            code, out = verify("report", root, "--json", agent="judge")
            self.assertEqual(len(json.loads(out)["gaps"]["not_independent"]), 1)

    def test_without_the_requirement_one_agent_may_do_both(self):
        with tempfile.TemporaryDirectory() as root:
            proved_repo(root, recipe=RECIPE.replace("require: independent\n\n", ""))
            self.assertEqual(verify("run", root, "--strict", agent="judge")[0], 0)

    def test_baseline_records_who_froze_each_check(self):
        with tempfile.TemporaryDirectory() as root:
            proved_repo(root)
            state = json.loads(Path(root, ".verify-state.json").read_text())
            self.assertEqual(state["frozen_by"], {"Answer|test|python check.py": "judge"})


if __name__ == "__main__":
    unittest.main()
