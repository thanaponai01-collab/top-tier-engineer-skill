"""1.12.0: Multi-agent swarm coordination (`verify.py swarm`), peer-swarm `verified_by`,
zero-file inline `challenge`, AST-validated manual challenges, `SIGNAL IN PASS` anti-gaming,
and polyglot (`JS/TS/Go`) per-test auditing.

Run with: python -m unittest discover tests
"""
import json, os, subprocess, sys, tempfile, unittest
from pathlib import Path

from _helpers import SCRIPTS, run


def run_as(agent, *args):
    env = os.environ.copy()
    if agent is None:
        env.pop("VERIFY_AGENT", None)
    else:
        env["VERIFY_AGENT"] = agent
    p = subprocess.run(
        [sys.executable, os.path.join(SCRIPTS["verify.py"], "verify.py"), *args],
        capture_output=True, text=True, encoding="utf-8", env=env,
    )
    return p.returncode, p.stdout, p.stderr


def git(root, *args):
    subprocess.run(["git", "-C", str(root), *args], check=True, capture_output=True)


def make_two_feature_repo(root):
    root = Path(root)
    (root / "auth.py").write_text("def check_token(tok):\n    return tok == 'secret'\n", encoding="utf-8")
    (root / "billing.py").write_text("def total(cents, tax):\n    return cents + tax\n", encoding="utf-8")
    (root / "test_auth.py").write_text(
        "from auth import check_token\n"
        "def test_check_token_rejects_bad():\n"
        "    assert check_token('secret') is True, 'AUTH_FAIL'\n"
        "    assert check_token('wrong') is False, 'AUTH_FAIL'\n"
        "if __name__ == '__main__':\n"
        "    test_check_token_rejects_bad()\n",
        encoding="utf-8",
    )
    (root / "test_billing.py").write_text(
        "from billing import total\n"
        "def test_total_adds_tax():\n"
        "    assert total(100, 15) == 115, 'BILLING_FAIL'\n"
        "if __name__ == '__main__':\n"
        "    test_total_adds_tax()\n",
        encoding="utf-8",
    )
    (root / "VERIFY.md").write_text(
        "## Auth\n"
        "- test: `python test_auth.py`\n"
        "- fail-signal: AUTH_FAIL\n"
        "- fail-proof: mutating auth.py check_token returns False on 'secret' and prints AUTH_FAIL\n\n"
        "## Billing\n"
        "- test: `python test_billing.py`\n"
        "- fail-signal: BILLING_FAIL\n"
        "- fail-proof: mutating billing.py total subtracts tax and prints BILLING_FAIL\n",
        encoding="utf-8",
    )
    git(root, "init", "-q")
    return root


class SwarmCoordination(unittest.TestCase):
    def test_work_stealing_claims_and_independence_routing(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = make_two_feature_repo(tmp)
            # Initially both features need a rejection receipt ("prove"), so swarm overview exits 1 ("pending")
            code, out, _ = run_as("alpha", "swarm", str(root), "--json")
            self.assertEqual(code, 1, out)
            plan = json.loads(out)
            self.assertEqual({t["feature"]: t["action"] for t in plan["items"]}, {"Auth": "prove", "Billing": "prove"})

            # Alpha claims first task (Auth)
            code, out, _ = run_as("alpha", "swarm", str(root), "--claim", "--json")
            self.assertEqual(code, 0, out)
            c1 = json.loads(out)["claimed"]
            self.assertEqual(c1["feature"], "Auth")
            self.assertEqual(c1["action"], "prove")

            # Beta claims next available task -> skips Auth (claimed by alpha) and gets Billing!
            code, out, _ = run_as("beta", "swarm", str(root), "--claim", "--json")
            self.assertEqual(code, 0, out)
            c2 = json.loads(out)["claimed"]
            self.assertEqual(c2["feature"], "Billing")

            # Gamma tries to claim while both are leased -> exits 3 ("waiting")
            code, out, _ = run_as("gamma", "swarm", str(root), "--claim", "--json")
            self.assertEqual(code, 3, out)
            self.assertIsNone(json.loads(out)["claimed"])

    def test_inline_challenge_and_peer_swarm_strict_green(self):
        """Two-agent peer swarm:
        - alpha challenges & freezes Auth
        - beta challenges & freezes Billing
        - alpha runs Billing & beta runs Auth (or each runs the suite) -> verified_by records independent proof
        - either agent can now pass `verify.py run --strict` without needing a 3rd agent!
        """
        with tempfile.TemporaryDirectory() as tmp:
            root = make_two_feature_repo(tmp)
            vmd = (root / "VERIFY.md").read_text(encoding="utf-8")
            (root / "VERIFY.md").write_text("require: independent\n\n" + vmd, encoding="utf-8")
            # Alpha proves Auth via zero-file inline challenge
            code, out, _ = run_as(
                "alpha", "challenge", str(root),
                "--feature", "Auth",
                "--file", "auth.py",
                "--before", "return tok == 'secret'",
                "--after", "return tok != 'secret'",
            )
            self.assertEqual(code, 0, out)
            self.assertIn("CHALLENGE: caught", out)

            # Beta proves Billing via zero-file inline challenge
            code, out, _ = run_as(
                "beta", "challenge", str(root),
                "--feature", "Billing",
                "--file", "billing.py",
                "--before", "return cents + tax",
                "--after", "return cents - tax",
            )
            self.assertEqual(code, 0, out)

            # Alpha freezes baseline
            self.assertEqual(run_as("alpha", "baseline", str(root))[0], 0)
            # Right after alpha freezes both, alpha alone CANNOT pass --strict because frozen_by == alpha:
            code, out, _ = run_as("alpha", "run", str(root), "--strict")
            self.assertEqual(code, 1, out)
            self.assertIn("NOT INDEPENDENT", out)

            # Swarm plan tells alpha that it cannot claim judge work on its own frozen checks, while beta can!
            code, out, _ = run_as("alpha", "swarm", str(root), "--claim", "--role", "judge", "--json")
            self.assertEqual(code, 3, out)
            code, out, _ = run_as("beta", "swarm", str(root), "--claim", "--role", "judge", "--json")
            self.assertEqual(code, 0, out)
            self.assertEqual(json.loads(out)["claimed"]["action"], "independent")

            # Once beta runs --strict, it records verified_by["Auth"] = beta and verified_by["Billing"] = beta
            code, out, _ = run_as("beta", "run", str(root), "--strict")
            self.assertEqual(code, 0, out)

            # And now EVEN alpha can run --strict and get green because verified_by holds beta's independent proof!
            code, out, _ = run_as("alpha", "run", str(root), "--strict")
            self.assertEqual(code, 0, out)
            # Swarm overview now reports green (exit 0)
            code, out, _ = run_as("alpha", "swarm", str(root), "--json")
            self.assertEqual(code, 0, out)
            self.assertEqual(json.loads(out)["verdict"], "green")

    def test_swarm_auto_surveys_all_mapped_features_in_shared_lane(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = make_two_feature_repo(tmp)
            code, out, _ = run_as("alpha", "swarm", str(root), "--auto", "--json")
            self.assertEqual(code, 0, out)
            report = json.loads(out)
            self.assertGreaterEqual(report["caught"], 2)
            self.assertEqual(report["survived"], 0)
            self.assertEqual({f["feature"] for f in report["features"]}, {"Auth", "Billing"})


class TrustAndAntiGaming(unittest.TestCase):
    def test_signal_printed_in_passing_output_is_rejected(self):
        """An agent cannot game fail-signal by picking text printed on every passing run."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "app.py").write_text("def ok():\n    return True\n", encoding="utf-8")
            # Test always prints BANNER_TEXT even when passing!
            (root / "check.py").write_text(
                "import sys\nfrom app import ok\nprint('BANNER_TEXT')\nif not ok():\n    sys.exit(1)\n",
                encoding="utf-8",
            )
            (root / "VERIFY.md").write_text(
                "## App\n"
                "- test: `python check.py`\n"
                "- fail-signal: BANNER_TEXT\n"
                "- fail-proof: when ok() is False check exits 1 and prints BANNER_TEXT\n",
                encoding="utf-8",
            )
            git(root, "init", "-q")
            # Inline challenge mutates True -> False, check exits 1 and prints BANNER_TEXT,
            # BUT original passing run ALSO printed BANNER_TEXT -> must be rejected (exit 2)!
            code, out, _ = run_as(
                "alpha", "challenge", str(root),
                "--feature", "App",
                "--file", "app.py",
                "--before", "return True",
                "--after", "return False",
            )
            self.assertEqual(code, 2, out)
            self.assertIn("SIGNAL IN PASS", out)

            # Even if an agent manually records a failure receipt first and then passes while printing BANNER_TEXT:
            (root / "app.py").write_text("def ok():\n    return False\n", encoding="utf-8")
            run_as("alpha", "run", str(root))  # records failure receipt with BANNER_TEXT
            (root / "app.py").write_text("def ok():\n    return True\n", encoding="utf-8")
            run_as("alpha", "baseline", str(root))
            code, out, _ = run_as("beta", "run", str(root), "--strict")
            self.assertEqual(code, 1, out)
            self.assertIn("SIGNAL IN PASS", out)

    def test_comment_only_and_syntax_error_challenges_are_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = make_two_feature_repo(tmp)
            # Comment-only mutation (AST unchanged)
            code, out, _ = run_as(
                "alpha", "challenge", str(root),
                "--feature", "Auth",
                "--file", "auth.py",
                "--before", "return tok == 'secret'",
                "--after", "return tok == 'secret'  # mutated comment",
            )
            self.assertEqual(code, 2, out)
            self.assertIn("changes only comments or formatting", out)

            # Syntax-error mutation
            code, out, _ = run_as(
                "alpha", "challenge", str(root),
                "--feature", "Auth",
                "--file", "auth.py",
                "--before", "return tok == 'secret'",
                "--after", "return tok ===",
            )
            self.assertEqual(code, 2, out)
            self.assertIn("syntax error", out)


class PolyglotTestAudit(unittest.TestCase):
    def test_js_and_go_hollow_tests_flagged_by_tests_strict(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "VERIFY.md").write_text(
                "## WebAuth\n"
                "- test: `node auth.test.js`\n"
                "- fail-signal: AssertionError\n"
                "- fail-proof: bad token throws AssertionError\n\n"
                "## GoStore\n"
                "- test: `go test ./...`\n"
                "- fail-signal: FAIL\n"
                "- fail-proof: broken store fails TestStoreSave\n",
                encoding="utf-8",
            )
            (root / "auth.test.js").write_text(
                "test('validates webauth token', () => {\n"
                "  expect(1 + 1).toBe(2);\n"
                "});\n"
                "test('hollow webauth check', () => {\n"
                "  const x = 42;\n"
                "});\n",
                encoding="utf-8",
            )
            (root / "store_test.go").write_text(
                "package store\n"
                "import \"testing\"\n"
                "func TestStoreSave(t *testing.T) {\n"
                "    if 1 != 1 { t.Fatalf(\"bad\") }\n"
                "}\n"
                "func TestStoreHollow(t *testing.T) {\n"
                "    _ = 1 + 1\n"
                "}\n",
                encoding="utf-8",
            )
            code, out, _ = run("verify.py", "tests", str(root), "--strict")
            self.assertEqual(code, 1, out)
            self.assertIn("hollow webauth check", out)
            self.assertIn("TestStoreHollow", out)
            self.assertIn("no assertion", out)


if __name__ == "__main__":
    unittest.main()
