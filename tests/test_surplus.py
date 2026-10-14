#!/usr/bin/env python3
"""
surplus.py — the repeat and mutate probes behind surplus.

Run them all with `python -m unittest discover tests`.
"""
import os, sys, tempfile, unittest

from _helpers import run

PRICE = "def free_shipping(total):\n    return total >= 50\n"
TEST_NO_BOUNDARY = ("import unittest\nfrom price import free_shipping\n"
                    "class T(unittest.TestCase):\n"
                    "    def test_small(self): self.assertFalse(free_shipping(10))\n"
                    "    def test_big(self): self.assertTrue(free_shipping(90))\n")
TEST_BOUNDARY = TEST_NO_BOUNDARY + "    def test_edge(self): self.assertTrue(free_shipping(50))\n"


def write(root, rel, text):
    with open(os.path.join(root, rel), "w", encoding="utf-8", newline="\n") as fh:
        fh.write(text)


def read(root, rel):
    with open(os.path.join(root, rel), encoding="utf-8") as fh:
        return fh.read()


class Mutate(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.dir = self._tmp.name
        write(self.dir, "price.py", PRICE)

    def mutate(self, *extra):
        return run("surplus.py", "mutate", "price.py", "--cwd", self.dir, *extra,
                   "--", sys.executable, "-m", "unittest")

    def test_an_unpinned_boundary_survives(self):
        write(self.dir, "test_price.py", TEST_NO_BOUNDARY)
        code, out, _ = self.mutate()
        self.assertEqual(code, 1, out)
        self.assertIn("SURVIVED price.py:2", out)
        self.assertIn(">= to >", out)

    def test_the_boundary_test_kills_it(self):
        write(self.dir, "test_price.py", TEST_BOUNDARY)
        code, out, _ = self.mutate()
        self.assertEqual(code, 0, out)
        self.assertNotIn("SURVIVED", out)

    def test_the_file_is_restored_byte_for_byte(self):
        write(self.dir, "test_price.py", TEST_NO_BOUNDARY)
        self.mutate()
        self.assertEqual(read(self.dir, "price.py"), PRICE)
        self.assertFalse(os.path.exists(os.path.join(self.dir, "price.py.surplus-orig")))

    def test_a_red_suite_is_refused(self):
        write(self.dir, "test_price.py", TEST_NO_BOUNDARY.replace("assertFalse(free", "assertTrue(free"))
        code, out, _ = self.mutate()
        self.assertEqual(code, 2, out)
        self.assertIn("failed on the untouched code", out)

    def test_a_flaky_kill_is_not_counted_as_killed(self):
        # The test fails on every second run, whatever the code: a kill it makes means nothing.
        write(self.dir, "test_price.py", TEST_NO_BOUNDARY.replace(
            "class T", "import os\nclass F(unittest.TestCase):\n"
            "    def test_alt(self):\n"
            "        n = int(open('n').read()) if os.path.exists('n') else 0\n"
            "        open('n', 'w').write(str(n + 1))\n"
            "        self.assertTrue(n < 3 or n % 2 == 0)\n"
            "class T"))
        code, out, _ = self.mutate()
        self.assertEqual(code, 1, out)
        self.assertIn("FLAKY KILL price.py:2", out)

    def test_a_leftover_backup_blocks_until_restored(self):
        write(self.dir, "test_price.py", TEST_BOUNDARY)
        write(self.dir, "price.py.surplus-orig", PRICE)
        write(self.dir, "price.py", PRICE.replace(">=", ">"))
        code, out, _ = self.mutate()
        self.assertEqual(code, 2, out)
        code, out, _ = run("surplus.py", "mutate", "price.py", "--cwd", self.dir, "--restore")
        self.assertEqual(code, 0, out)
        self.assertEqual(read(self.dir, "price.py"), PRICE)

    def test_strings_and_comments_are_not_mutated(self):
        write(self.dir, "price.py", '# total >= 50 ships free\nLABEL = "a >= b"\n' + PRICE)
        write(self.dir, "test_price.py", TEST_BOUNDARY)
        code, out, _ = self.mutate()
        self.assertIn("1 mutants", out)


class Repeat(unittest.TestCase):
    def test_counts_failures_and_names_a_flake(self):
        with tempfile.TemporaryDirectory() as d:
            write(d, "check.py", "import os\nn = int(open('n').read()) if os.path.exists('n') else 0\n"
                                 "open('n', 'w').write(str(n + 1))\nraise SystemExit(1 if n % 3 == 2 else 0)\n")
            code, out, _ = run("surplus.py", "repeat", "--times", "6", "--cwd", d,
                               "--", sys.executable, "check.py")
        self.assertEqual(code, 1, out)
        self.assertIn("4/6 passed, 2 failed", out)
        self.assertIn("FLAKY", out)

    def test_a_steady_green_exits_zero(self):
        with tempfile.TemporaryDirectory() as d:
            code, out, _ = run("surplus.py", "repeat", "--times", "3", "--cwd", d,
                               "--", sys.executable, "-c", "pass")
        self.assertEqual(code, 0, out)
        self.assertIn("3/3 passed", out)

    def test_always_red_is_not_called_flaky(self):
        with tempfile.TemporaryDirectory() as d:
            code, out, _ = run("surplus.py", "repeat", "--times", "2", "--cwd", d,
                               "--", sys.executable, "-c", "raise SystemExit(1)")
        self.assertEqual(code, 1, out)
        self.assertIn("RED on every run", out)


if __name__ == "__main__":
    unittest.main()
