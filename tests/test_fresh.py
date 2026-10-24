"""1.21.0: a feature with `fresh: N` re-runs its passing checks with N random VERIFY_SEED values, so
product code that special-cases the inputs its check was written with is OVERFIT, not green.

Run with: python -m unittest discover tests
"""
import json, tempfile, unittest
from pathlib import Path

from _helpers import run

HONEST = "def apply_refund(credit, amount):\n    return credit + amount\n"
# Passes the one case the check was written with and nothing else.
GAMED = ("def apply_refund(credit, amount):\n    if (credit, amount) == (100, 50):\n        return 150\n"
         "    return credit\n")
# The own case comes from the fixture; a seed draws fresh ones, the expected value from the spec.
SEEDED = ("import os, random\nfrom refund import apply_refund\n"
          "seed = os.environ.get('VERIFY_SEED')\n"
          "if seed:\n    rng = random.Random(int(seed))\n"
          "    cases = [(rng.randint(1, 10**6), rng.randint(1, 10**6)) for _ in range(5)]\n"
          "else:\n    cases = [(100, 50)]\n"
          "for credit, amount in cases:\n    got = apply_refund(credit, amount)\n"
          "    assert got == credit + amount, f'refund credit mismatch: {credit}+{amount} gave {got}'\n")
FIXED = ("from refund import apply_refund\n"
         "assert apply_refund(100, 50) == 150, 'refund credit mismatch'\n")


def write(root, rel, text):
    p = Path(root, rel)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text, encoding="utf-8")


def project(root, product=GAMED, test=SEEDED, fresh="- fresh: 3\n"):
    write(root, "refund.py", product)
    write(root, "test_refund.py", test)
    write(root, "VERIFY.md", "## Refunds\n- path: refund.py\n- test: `python test_refund.py`\n"
                             "- fail-signal: refund credit mismatch\n" + fresh)


class Fresh(unittest.TestCase):
    def test_special_cased_product_is_overfit_and_red(self):
        with tempfile.TemporaryDirectory() as root:
            project(root)
            code, out, _ = run("verify.py", "run", root)
            self.assertEqual(code, 1, out)
            self.assertIn("OVERFIT", out)
            self.assertIn("VERIFY_SEED=", out)
            self.assertIn("refund credit mismatch", out)
            self.assertIn("| 1 overfit", out)
            code, out, _ = run("verify.py", "run", root, "--json")
            self.assertEqual(code, 1, out)
            self.assertEqual(json.loads(out)["summary"]["overfit"], ["Refunds"])

    def test_overfit_is_never_hidden_by_the_cache(self):
        with tempfile.TemporaryDirectory() as root:
            project(root)
            run("verify.py", "run", root)
            code, out, _ = run("verify.py", "run", root)
            self.assertEqual(code, 1, out)
            self.assertIn("OVERFIT", out)

    def test_honest_product_passes_fresh_inputs(self):
        with tempfile.TemporaryDirectory() as root:
            project(root, product=HONEST)
            code, out, _ = run("verify.py", "run", root)
            self.assertEqual(code, 0, out)
            self.assertIn("FRESH  3 seeded run(s) passed", out)
            self.assertNotIn("OVERFIT", out)
            self.assertIn("1 checks pass", out)  # `fresh:` is not a check of its own

    def test_without_fresh_the_gamed_product_passes(self):
        """The guard is opt-in: fixed cases alone cannot tell a special case from the behavior."""
        with tempfile.TemporaryDirectory() as root:
            project(root, fresh="")
            code, out, _ = run("verify.py", "run", root)
            self.assertEqual(code, 0, out)
            self.assertNotIn("OVERFIT", out)

    def test_fresh_on_a_check_that_ignores_the_seed_is_red(self):
        with tempfile.TemporaryDirectory() as root:
            project(root, test=FIXED)
            code, out, _ = run("verify.py", "run", root)
            self.assertEqual(code, 1, out)
            self.assertIn("SEED UNUSED", out)

    def test_seed_read_by_an_oracle_helper_counts(self):
        with tempfile.TemporaryDirectory() as root:
            project(root, product=HONEST, test="from cases import cases\n" + SEEDED.split("seed = ")[0]
                    + "for credit, amount in cases():\n    assert apply_refund(credit, amount) == credit + amount, "
                    "'refund credit mismatch'\n")
            write(root, "cases.py", "import os, random\ndef cases():\n    s = os.environ.get('VERIFY_SEED')\n"
                                    "    if not s:\n        return [(100, 50)]\n    r = random.Random(int(s))\n"
                                    "    return [(r.randint(1, 99), r.randint(1, 99))]\n")
            write(root, "VERIFY.md", Path(root, "VERIFY.md").read_text() + "- oracle: cases.py\n")
            code, out, _ = run("verify.py", "run", root)
            self.assertEqual(code, 0, out)
            self.assertNotIn("SEED UNUSED", out)

    def test_bad_fresh_count_is_broken(self):
        with tempfile.TemporaryDirectory() as root:
            project(root, product=HONEST, fresh="- fresh: lots\n")
            code, out, _ = run("verify.py", "run", root)
            self.assertEqual(code, 1, out)
            self.assertIn("BROKEN  fresh:", out)

    def test_own_cases_run_without_a_seed_even_if_one_is_set_outside(self):
        import os, subprocess, sys
        from _helpers import SCRIPTS
        with tempfile.TemporaryDirectory() as root:
            project(root, fresh="")
            env = dict(os.environ, VERIFY_SEED="7")
            p = subprocess.run([sys.executable, os.path.join(SCRIPTS["verify.py"], "verify.py"), "run", root],
                               capture_output=True, text=True, encoding="utf-8", env=env)
            self.assertEqual(p.returncode, 0, p.stdout)

    def test_overfit_is_a_fix_step(self):
        with tempfile.TemporaryDirectory() as root:
            project(root)
            run("verify.py", "run", root)
            _, out, _ = run("verify.py", "report", root)
            self.assertIn("NEXT  Refunds [fix]", out)
            self.assertIn("OVERFIT", out)

    def test_removing_fresh_after_baseline_is_check_changed(self):
        with tempfile.TemporaryDirectory() as root:
            project(root, product=HONEST)
            run("verify.py", "baseline", root)
            project(root, product=HONEST, fresh="")
            _, out, _ = run("verify.py", "run", root)
            self.assertIn("CHECK CHANGED", out)

    def test_raising_fresh_is_not_a_weakening(self):
        with tempfile.TemporaryDirectory() as root:
            project(root, product=HONEST)
            run("verify.py", "baseline", root)
            project(root, product=HONEST, fresh="- fresh: 5\n")
            code, out, _ = run("verify.py", "baseline", root)
            self.assertEqual(code, 0, out)


class RequireFresh(unittest.TestCase):
    """1.22.0: `require: fresh` makes strict red for a feature that declares no `fresh:`."""

    def recipe(self, root, fresh):
        project(root, product=HONEST, fresh=fresh)
        Path(root, "VERIFY.md").write_text("require: fresh\n\n" + Path(root, "VERIFY.md").read_text())

    def test_strict_is_red_without_fresh(self):
        with tempfile.TemporaryDirectory() as root:
            self.recipe(root, "")
            code, out, _ = run("verify.py", "run", root, "--strict")
            self.assertEqual(code, 1, out)
            self.assertIn("NO FRESH INPUTS  Refunds", out)
            _, out, _ = run("verify.py", "report", root)
            self.assertIn("GAP  no fresh inputs: Refunds", out)
            self.assertIn("NEXT  Refunds [map]", out)
            self.assertIn("fresh:", out.split("NEXT  Refunds [map]")[1])

    def test_declared_fresh_clears_it(self):
        with tempfile.TemporaryDirectory() as root:
            self.recipe(root, "- fresh: 2\n")
            _, out, _ = run("verify.py", "run", root, "--strict")
            self.assertNotIn("NO FRESH INPUTS", out)

    def test_not_required_without_the_word(self):
        with tempfile.TemporaryDirectory() as root:
            project(root, product=HONEST, fresh="")
            _, out, _ = run("verify.py", "run", root, "--strict")
            self.assertNotIn("NO FRESH INPUTS", out)

    def test_json_counts_it(self):
        with tempfile.TemporaryDirectory() as root:
            self.recipe(root, "")
            _, out, _ = run("verify.py", "run", root, "--strict", "--json")
            self.assertEqual(json.loads(out)["summary"]["no_fresh"], ["Refunds"])


if __name__ == "__main__":
    unittest.main()
