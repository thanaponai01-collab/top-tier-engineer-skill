"""diet.py - the leads it lists, and the done check that refuses a slimmer suite that lost something.

Each test plants the thing a rule exists to catch, so disabling that rule turns it red.
Run them all with `python -m unittest discover tests`.
"""
import json, os, shutil, tempfile, unittest

from _helpers import ROOT, run

TESTS = "python -m unittest discover -s tests -t ."
CART = '''class Cart:
    def __init__(self, user):
        self.user = user
        self.items = []
        self.paid = False

    def add(self, name, price, qty=1):
        if qty < 1:
            raise ValueError("qty")
        self.items.append((name, price, qty))

    def total(self):
        t = sum(p * q for _, p, q in self.items)
        if t > 100:
            t = t - 10
        return t

    def pay(self, gateway):
        if not self.items:
            raise ValueError("empty")
        gateway.charge(self.user, self.total())
        self.paid = True


def make_user(name, verified=False):
    return {"name": name, "verified": verified}
'''
OLD_TESTS = '''import time
import unittest
from unittest import mock
from shop.cart import Cart, make_user


class TestCart(unittest.TestCase):
    def test_total(self):
        u = make_user("ann", verified=True)
        c = Cart(u)
        c.add("pen", 3)
        c.add("ink", 5, 2)
        self.assertEqual(c.total(), 13)

    def test_discount(self):
        user = make_user("bob", verified=True)
        cart = Cart(user)
        cart.add("pen", 3)
        cart.add("desk", 120)
        self.assertEqual(cart.total(), 113)

    def test_pay(self):
        x = make_user("cy", verified=True)
        y = Cart(x)
        y.add("pen", 3)
        y.add("ink", 5, 2)
        time.sleep(0.3)
        g = mock.Mock()
        y.pay(g)
        g.charge.assert_called_once()

    def test_pay_marks_paid(self):
        x = make_user("cy", verified=True)
        y = Cart(x)
        y.add("pen", 3)
        y.add("ink", 5, 2)
        y.pay(mock.Mock())
        self.assertTrue(y.paid)

    def test_empty(self):
        c = Cart(make_user("d"))
        with self.assertRaises(ValueError):
            c.pay(mock.Mock())
'''
NEW_TESTS = '''import unittest
from unittest import mock
from shop.cart import Cart, make_user


def cart_with(*items):
    c = Cart(make_user("ann", verified=True))
    for item in items:
        c.add(*item)
    return c


class TestCart(unittest.TestCase):
    def test_total(self):
        self.assertEqual(cart_with(("pen", 3), ("ink", 5, 2)).total(), 13)

    def test_discount(self):
        self.assertEqual(cart_with(("pen", 3), ("desk", 120)).total(), 113)

    def test_pay_charges_and_marks_paid(self):
        c, g = cart_with(("pen", 3), ("ink", 5, 2)), mock.Mock()
        c.pay(g)
        g.charge.assert_called_once_with(c.user, 13)
        self.assertTrue(c.paid)

    def test_empty(self):
        with self.assertRaises(ValueError):
            cart_with().pay(mock.Mock())
'''
PAY = "tests/test_cart.py::TestCart::test_pay"


def write(root, rel, text):
    p = os.path.join(root, *rel.split("/"))
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, "w", encoding="utf-8") as fh:
        fh.write(text)


class Repo(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.root = os.path.join(self._tmp.name, "repo")
        for rel, text in {"shop/__init__.py": "", "shop/cart.py": CART, "tests/__init__.py": "",
                          "tests/test_cart.py": OLD_TESTS}.items():
            write(self.root, rel, text)

    def d(self, *args):
        return run("diet.py", self.root, *args)

    def record(self, *extra):
        code, out, err = self.d("--run", TESTS, *extra)
        self.assertEqual(code, 0, out + err)
        with open(os.path.join(self.root, ".diet", "record.json"), encoding="utf-8") as fh:
            self.rec = json.load(fh)
        return out

    def setup_id(self):
        return next(l["id"] for l in self.rec["leads"] if l["kind"] == "setup")

    def good_plan(self):
        return {"changes": [
            {"covers": [self.setup_id()], "what": "cart_with() builds each cart", "at": "tests/test_cart.py:cart_with"},
            {"covers": ["slow:" + PAY, "mock:" + PAY], "what": "merged test_pay, no sleep, checks the amount"}],
            "kept": []}

    def slim(self, tests=NEW_TESTS, plan=None):
        write(self.root, "tests/test_cart.py", tests)
        write(self.root, ".diet/plan.json", json.dumps(plan or self.good_plan()))

    def refused(self, needle):
        code, out, err = self.d("--done")
        self.assertEqual(code, 1, out + err)
        self.assertIn("DIET: refused", out)
        self.assertIn(needle, out)
        return out


class Find(Repo):
    def test_repeated_setup_lists_every_copy_and_the_calls_it_replays(self):
        out = self.d()[1]
        self.assertIn("repeated in 4 places; replays: make_user -> Cart -> add", out)
        for t in ("test_total", "test_discount", "test_pay ", "test_pay_marks_paid"):
            self.assertIn(t, out)

    def test_names_and_literals_do_not_hide_a_copy(self):
        # test_discount uses other names and values; its first three statements still match test_total's
        write(self.root, "tests/test_cart.py", OLD_TESTS.replace('cart.add("desk", 120)', 'cart.add("desk", 120, 1)'))
        self.assertIn("test_discount", self.d()[1].split("## mock")[0])

    def test_a_test_that_only_checks_mocks_is_a_lead(self):
        out = self.d()[1]
        self.assertIn("## mock:" + PAY, out)
        self.assertNotIn("## mock:tests/test_cart.py::TestCart::test_pay_marks_paid", out)

    def test_a_sleep_is_a_slow_lead_before_timing(self):
        self.assertIn("sleeps (line 27)", self.d()[1])

    def test_timing_marks_a_slow_test(self):
        self.record()
        slow = [l for l in self.rec["leads"] if l["id"] == "slow:" + PAY][0]
        self.assertGreaterEqual(slow["seconds"], 0.25)
        self.assertLess(self.rec["times"]["tests/test_cart.py::TestCart::test_total"], 0.25)

    def test_planted_bugs_are_recorded_with_what_the_suite_caught(self):
        self.record()
        self.assertTrue(self.rec["mutants"])
        self.assertTrue(set(self.rec["caught"]) <= {m["id"] for m in self.rec["mutants"]})
        self.assertTrue(all(m["path"] == "shop/cart.py" for m in self.rec["mutants"]))
        self.assertGreater(len(self.rec["caught"]), 0)

    def test_repeated_lines_in_other_languages_are_found(self):
        block = "  const u = makeUser('a');\n  const c = new Cart(u);\n  c.add('pen', 3);\n  c.add('ink', 5);\n"
        write(self.root, "web/cart.test.js", "test('a', () => {\n" + block + "  expect(c.total()).toBe(13);\n});\n"
              "test('b', () => {\n" + block.replace("'a'", "'b'") + "  expect(c.items.length).toBe(2);\n});\n")
        out = self.d()[1]
        self.assertIn("5 lines repeated in 2 places", out)
        self.assertIn("web/cart.test.js:1", out)
        self.assertIn("web/cart.test.js:8", out)

    def test_a_red_suite_is_not_recorded(self):
        write(self.root, "tests/test_cart.py", OLD_TESTS.replace("13)", "14)"))
        code, out, _ = self.d("--run", TESTS)
        self.assertEqual(code, 1)
        self.assertIn("the tests fail before any change", out)

    def test_a_command_that_runs_no_countable_tests_is_refused(self):
        code, out, _ = self.d("--run", "python -c \"print('hi')\"")
        self.assertEqual(code, 1)
        self.assertIn("ran no tests I could count", out)

    @unittest.skipUnless(shutil.which("pytest"), "pytest not installed")
    def test_pytest_is_timed_per_test(self):
        code, out, err = self.d("--run", "pytest -q tests", "--mutants", "0")
        self.assertEqual(code, 0, out + err)
        with open(os.path.join(self.root, ".diet", "record.json"), encoding="utf-8") as fh:
            rec = json.load(fh)
        self.assertGreaterEqual(rec["times"][PAY], 0.25)


class Recorded(Repo):
    MUTANTS = "0"  # planted bugs are slow to run; only the Mutants class asks for them

    def setUp(self):
        super().setUp()
        self.record("--mutants", self.MUTANTS)


class Done(Recorded):

    def test_no_record_is_refused(self):
        shutil.rmtree(os.path.join(self.root, ".diet"))
        code, out, _ = self.d("--done")
        self.assertEqual(code, 1)
        self.assertIn("no record", out)

    def test_no_plan_is_refused(self):
        code, out, _ = self.d("--done")
        self.assertEqual(code, 1)
        self.assertIn("plan.json is missing", out)

    def test_a_lead_neither_covered_nor_kept_is_refused(self):
        plan = self.good_plan()
        plan["changes"][1]["covers"] = ["slow:" + PAY]
        self.slim(plan=plan)
        self.refused("mock:" + PAY + " is neither covered")

    def test_kept_needs_a_reason(self):
        plan = self.good_plan()
        plan["changes"][1]["covers"] = ["slow:" + PAY]
        plan["kept"] = [{"candidate": "mock:" + PAY, "why": " "}]
        self.slim(plan=plan)
        self.refused("with no reason")

    def test_a_kept_lead_with_a_reason_is_done(self):
        plan = self.good_plan()
        plan["changes"][1]["covers"] = ["slow:" + PAY]
        plan["kept"] = [{"candidate": "mock:" + PAY, "why": "the gateway call is the behavior"}]
        self.slim(plan=plan)
        code, out, err = self.d("--done")
        self.assertEqual(code, 0, out + err)

    def test_a_change_must_say_what(self):
        plan = self.good_plan()
        plan["changes"][0]["what"] = ""
        self.slim(plan=plan)
        self.refused("says nothing in `what`")

    def test_covered_setup_still_repeated_is_refused(self):
        self.slim(tests=OLD_TESTS.replace("        time.sleep(0.3)\n", "").replace(
            "        g.charge.assert_called_once()", "        g.charge.assert_called_once()\n        self.assertTrue(y.paid)"))
        self.refused("is covered but part of it is still repeated")

    def test_covered_slow_test_that_is_not_faster_is_refused(self):
        self.slim(tests=NEW_TESTS.replace("    def test_pay_charges_and_marks_paid", "    def test_pay")
                  .replace("        c.pay(g)\n", "        c.pay(g)\n        import time; time.sleep(0.3)\n"))
        self.refused("slow:" + PAY + " is covered but takes")

    def test_covered_mock_only_test_that_still_checks_only_mocks_is_refused(self):
        self.slim(tests=NEW_TESTS.replace("    def test_pay_charges_and_marks_paid", "    def test_pay")
                  .replace("        self.assertTrue(c.paid)\n", ""))
        self.refused("still checks only mocks")

    def test_an_app_change_is_refused(self):
        self.slim()
        write(self.root, "shop/cart.py", CART + "\n# tidy\n")
        self.refused("app file shop/cart.py changed")

    def test_a_new_app_file_is_refused(self):
        self.slim()
        write(self.root, "shop/factories.py", "X = 1\n")
        self.refused("app file shop/factories.py is new")

    def test_a_removed_app_file_is_refused(self):
        self.slim()
        os.remove(os.path.join(self.root, "shop", "__init__.py"))
        self.refused("app file shop/__init__.py went away")

    def test_failing_tests_are_refused(self):
        self.slim(tests=NEW_TESTS.replace("13)", "14)"))
        self.refused("the tests passed before and fail now")

    def test_longer_tests_are_refused(self):
        self.slim(tests=NEW_TESTS + "\n" + "\n".join(f"X{i} = {i}" for i in range(40)) + "\n")
        self.refused("the tests got longer")

    def test_slower_tests_are_refused(self):
        self.slim(tests=NEW_TESTS.replace("    def test_empty(self):\n",
                                          "    def test_empty(self):\n        import time; time.sleep(2)\n"))
        self.refused("the tests got slower")

class Mutants(Recorded):
    MUTANTS = "20"

    def test_a_good_diet_is_done_with_numbers_before_and_after(self):
        self.slim()
        code, out, err = self.d("--done")
        self.assertEqual(code, 0, out + err)
        self.assertIn("DIET: done", out)
        with open(os.path.join(self.root, ".diet", "REPORT.md"), encoding="utf-8") as fh:
            report = fh.read()
        self.assertIn("| test lines |", report)
        self.assertIn("| planted bugs caught |", report)

    def test_a_planted_bug_the_old_tests_caught_and_the_new_miss_is_refused(self):
        without_discount = NEW_TESTS.replace(
            '    def test_discount(self):\n        self.assertEqual(cart_with(("pen", 3), ("desk", 120)).total(), 113)\n\n', "")
        self.slim(tests=without_discount)
        out = self.refused("a planted bug the old tests caught is missed now")
        self.assertIn("shop/cart.py:15", out)


class Skill(unittest.TestCase):
    def test_skill_is_short_manual_and_names_its_helper(self):
        with open(os.path.join(ROOT, "plugin", "skills", "test-diet", "SKILL.md"), encoding="utf-8") as fh:
            text = fh.read()
        head, body = text.split("---", 2)[1:]
        self.assertIn("disable-model-invocation: true", head)
        self.assertLessEqual(len(body), 3000)
        self.assertIn("scripts/diet.py", body)
        self.assertIn("--done", body)
        self.assertIn(".diet/plan.json", body)


if __name__ == "__main__":
    unittest.main()
