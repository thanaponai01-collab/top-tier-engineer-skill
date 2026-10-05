"""Exercise the challenge mode through the public verify CLI."""
import json
import tempfile
import unittest
from pathlib import Path

from _helpers import run


class Challenge(unittest.TestCase):
    def fixture(self, root, check="assert answer() == 42, 'expected 42'"):
        Path(root, "app.py").write_text("def answer(): return 42\n")
        Path(root, "test_answer.py").write_text("from app import answer\n" + check + "\n")
        Path(root, "VERIFY.md").write_text(
            "## Answer\n- test: `python test_answer.py`\n- fail-signal: expected 42\n")
        Path(root, "mutation.json").write_text(json.dumps(
            {"file": "app.py", "before": "return 42", "after": "return 41",
             "claim": "the answer must equal 42"}))

    def challenge(self, root):
        return run("verify.py", "challenge", root, "--feature", "Answer",
                   "--mutation", str(Path(root, "mutation.json")))

    def test_catches_mutation_without_touching_original_or_regular_run_state(self):
        with tempfile.TemporaryDirectory() as root:
            self.fixture(root)
            run("verify.py", "run", root)
            before = json.loads(Path(root, ".verify-state.json").read_text())
            code, out, err = self.challenge(root)
            self.assertEqual(code, 0, out + err)
            self.assertIn("CHALLENGE: caught", out)
            self.assertEqual(Path(root, "app.py").read_text(), "def answer(): return 42\n")
            after = json.loads(Path(root, ".verify-state.json").read_text())
            self.assertEqual({k: v for k, v in after.items() if k not in ("challenge", "failures")},
                             {k: v for k, v in before.items() if k != "failures"})
            self.assertIn("Answer|python test_answer.py", after["failures"])
            self.assertIn("expected 42", after["challenge"]["mutated"]["checks"]["Answer|python test_answer.py"]["output"])

    def test_reports_surviving_mutation(self):
        with tempfile.TemporaryDirectory() as root:
            self.fixture(root, "assert 42 == 42")
            code, out, _ = self.challenge(root)
            self.assertEqual(code, 1, out)
            self.assertIn("CHALLENGE: survived", out)

    def test_caught_challenge_supplies_rejection_evidence_to_strict_loop(self):
        with tempfile.TemporaryDirectory() as root:
            self.fixture(root)
            recipe = Path(root, "VERIFY.md")
            recipe.write_text(recipe.read_text() + "- fail-proof: replaced answer 42 with 41 in scratch\n")
            run("verify.py", "baseline", root)
            self.assertEqual(self.challenge(root)[0], 0)
            code, out, err = run("verify.py", "run", root, "--strict")
            self.assertEqual(code, 0, out + err)
            self.assertEqual(run("verify.py", "status", root)[0], 0)

    def test_changed_signal_invalidates_challenge_evidence(self):
        with tempfile.TemporaryDirectory() as root:
            self.fixture(root)
            self.assertEqual(self.challenge(root)[0], 0)
            recipe = Path(root, "VERIFY.md")
            recipe.write_text(recipe.read_text().replace("expected 42", "new expectation")
                              + "- fail-proof: prior challenge caught the error\n")
            run("verify.py", "baseline", root)
            self.assertEqual(run("verify.py", "run", root, "--strict")[0], 1)

    def test_harness_failure_is_inconclusive_even_when_signal_matches(self):
        with tempfile.TemporaryDirectory() as root:
            self.fixture(root)
            mutation = json.loads(Path(root, "mutation.json").read_text())
            mutation["after"] = "raise ImportError('expected 42')"
            Path(root, "mutation.json").write_text(json.dumps(mutation))
            code, out, _ = self.challenge(root)
            self.assertEqual(code, 2, out)
            self.assertIn("CHALLENGE: inconclusive", out)

    def test_rejects_frozen_target_and_nonunique_replacement(self):
        for field, value in (("file", "test_answer.py"), ("before", "absent")):
            with self.subTest(field=field), tempfile.TemporaryDirectory() as root:
                self.fixture(root)
                mutation = json.loads(Path(root, "mutation.json").read_text())
                mutation[field] = value
                Path(root, "mutation.json").write_text(json.dumps(mutation))
                code, out, _ = self.challenge(root)
                self.assertEqual(code, 2, out)
                self.assertFalse(Path(root, ".verify-state.json").exists())

    def test_red_original_does_not_prove_mutation_detection(self):
        with tempfile.TemporaryDirectory() as root:
            self.fixture(root, "assert False, 'expected 42'")
            code, out, _ = self.challenge(root)
            self.assertEqual(code, 2, out)
            self.assertIn("CHALLENGE: inconclusive", out)

    def test_rejects_path_outside_repo(self):
        with tempfile.TemporaryDirectory() as root:
            self.fixture(root)
            mutation = json.loads(Path(root, "mutation.json").read_text())
            mutation["file"] = "../outside.py"
            Path(root, "mutation.json").write_text(json.dumps(mutation))
            self.assertEqual(self.challenge(root)[0], 2)

    def test_check_cannot_erase_mutation_and_call_it_a_survivor(self):
        with tempfile.TemporaryDirectory() as root:
            self.fixture(root, "open('app.py', 'w').write('def answer(): return 42\\n')")
            code, out, err = self.challenge(root)
            self.assertEqual(code, 2, out + err)
            self.assertIn("mutated product changed", out)

    def test_missing_feature_signal_is_invalid(self):
        with tempfile.TemporaryDirectory() as root:
            self.fixture(root)
            recipe = Path(root, "VERIFY.md")
            recipe.write_text(recipe.read_text().replace("- fail-signal: expected 42\n", ""))
            code, out, _ = self.challenge(root)
            self.assertEqual(code, 2, out)
            self.assertIn("declared fail-signal", out)

    def test_challenge_proof_is_limited_to_the_selected_feature(self):
        with tempfile.TemporaryDirectory() as root:
            self.fixture(root)
            Path(root, "test_second.py").write_text("from app import answer\nassert answer() == 42, 'expected 42'\n")
            recipe = Path(root, "VERIFY.md")
            recipe.write_text(recipe.read_text() + "- fail-proof: answer mutation\n"
                              "## Second\n- test: `python test_second.py`\n"
                              "- fail-signal: expected 42\n- fail-proof: second feature claimed red\n")
            run("verify.py", "baseline", root)
            self.assertEqual(self.challenge(root)[0], 0)
            code, out, _ = run("verify.py", "run", root, "--strict")
            self.assertEqual(code, 1, out)
            self.assertIn("1 unproven", out)

    def test_sequential_challenges_preserve_proof_for_both_features(self):
        with tempfile.TemporaryDirectory() as root:
            self.fixture(root)
            Path(root, "test_second.py").write_text("from app import answer\nassert answer() == 42, 'expected 42'\n")
            recipe = Path(root, "VERIFY.md")
            recipe.write_text(recipe.read_text() + "- fail-proof: answer mutation\n"
                              "## Second\n- test: `python test_second.py`\n"
                              "- fail-signal: expected 42\n- fail-proof: second feature mutation\n")
            run("verify.py", "baseline", root)
            self.assertEqual(self.challenge(root)[0], 0)
            code, out, err = run("verify.py", "challenge", root, "--feature", "Second",
                                 "--mutation", str(Path(root, "mutation.json")))
            self.assertEqual(code, 0, out + err)
            code, out, err = run("verify.py", "run", root, "--strict")
            self.assertEqual(code, 0, out + err)
            self.assertEqual(run("verify.py", "status", root)[0], 0)
