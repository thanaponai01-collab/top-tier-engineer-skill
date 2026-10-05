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


class AutoChallenge(unittest.TestCase):
    """challenge --auto: generated mutations, a score, and no receipts."""

    def fixture(self, root, check):
        Path(root, "app.py").write_text(
            "def grade(score):\n    if score >= 50:\n        return 'pass'\n    return 'fail'\n")
        Path(root, "test_grade.py").write_text("from app import grade\n" + check + "\n")
        Path(root, "VERIFY.md").write_text(
            "## Grade\n- test: `python test_grade.py`\n- fail-signal: expected\n")

    def auto(self, root, *extra):
        return run("verify.py", "challenge", root, "--feature", "Grade", "--auto", "app.py", *extra)

    def test_strong_check_catches_every_generated_mutation(self):
        with tempfile.TemporaryDirectory() as root:
            self.fixture(root, "assert grade(50) == 'pass', 'expected pass at 50'\n"
                               "assert grade(49) == 'fail', 'expected fail at 49'")
            code, out, err = self.auto(root, "--json")
            self.assertEqual(code, 0, out + err)
            summary = json.loads(out)
            self.assertGreaterEqual(summary["caught"], 2)
            self.assertEqual(summary["survived"], 0)
            self.assertEqual(summary["score"], 1.0)

    def test_weak_check_reports_survivors_and_records_no_receipts(self):
        with tempfile.TemporaryDirectory() as root:
            self.fixture(root, "assert grade(90) == 'pass', 'expected pass at 90'")
            code, out, err = self.auto(root)
            self.assertEqual(code, 1, out + err)
            self.assertIn("SURVIVED", out)
            self.assertIn("ge-to-gt", out)  # boundary 50 is never tested
            state = Path(root, ".verify-state.json")
            self.assertFalse(state.exists() and json.loads(state.read_text()).get("failures"))
            self.assertIn("score >= 50", Path(root, "app.py").read_text())

    def test_needs_exactly_one_of_mutation_or_auto(self):
        with tempfile.TemporaryDirectory() as root:
            self.fixture(root, "assert True")
            code, _, err = run("verify.py", "challenge", root, "--feature", "Grade")
            self.assertEqual(code, 2, err)
            self.assertIn("exactly one", err)

    def test_unknown_feature_is_invalid_not_a_score(self):
        with tempfile.TemporaryDirectory() as root:
            self.fixture(root, "assert grade(50) == 'pass', 'expected'")
            code, out, _ = run("verify.py", "challenge", root, "--feature", "Nope", "--auto", "app.py")
            self.assertEqual(code, 2, out)
            self.assertIn("score n/a", out)

    def test_ast_operators_and_syntax_validation(self):
        with tempfile.TemporaryDirectory() as root:
            Path(root, "calc.py").write_text("def mul(a, b):\n    return a * b\n")
            Path(root, "test_calc.py").write_text("from calc import mul\nassert mul(2, 3) == 6, 'expected 6'\n")
            Path(root, "VERIFY.md").write_text("## Calc\n- test: `python test_calc.py`\n- fail-signal: expected\n")
            code, out, err = run("verify.py", "challenge", root, "--feature", "Calc", "--auto", "calc.py", "--json")
            self.assertEqual(code, 0, out + err)
            summary = json.loads(out)
            ops = [r["operator"] for r in summary["results"]]
            self.assertIn("mul-to-div", ops)
            self.assertIn("return-to-none", ops)
            self.assertEqual(summary["survived"], 0)


class StatusJson(unittest.TestCase):
    def test_json_matches_text_verdict_and_exit(self):
        with tempfile.TemporaryDirectory() as root:
            code, out, _ = run("verify.py", "status", root, "--json")
            self.assertEqual((code, json.loads(out)["state"]), (0, "none"))
            Path(root, "VERIFY.md").write_text(
                "## A\n- test: `python -c \"import sys; print('expected 1, got 2'); sys.exit(1)\"`\n")
            code, out, _ = run("verify.py", "status", root, "--json")
            self.assertEqual((code, json.loads(out)["state"]), (3, "never-run"))
            run("verify.py", "run", root)
            code, out, _ = run("verify.py", "status", root, "--json")
            data = json.loads(out)
            self.assertEqual((code, data["state"], data["exit"]), (1, "red", 1))
            self.assertEqual(len(data["failing"]), 1)
            self.assertEqual(run("verify.py", "status", root)[0], code)
