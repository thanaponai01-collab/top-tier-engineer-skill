"""states.py - the candidates it lists, and the done check that refuses a map with a gap or a bug with no proof.

Each test plants the thing a rule exists to catch, so disabling that rule turns it red.
Run them all with `python -m unittest discover tests`.
"""
import json, os, tempfile, unittest

from _helpers import ROOT, run

TESTS = "python -m unittest discover -s tests -t ."
FILES = {
    "shop/__init__.py": "",
    "shop/order.py": ("class Order:\n"
                      "    def __init__(self):\n"
                      "        self.status = 'new'\n\n\n"
                      "def pay(o):\n"
                      "    if o.status != 'new':\n"
                      "        raise ValueError(o.status)\n"
                      "    o.status = 'paid'\n\n\n"
                      "def cancel(o):\n"
                      "    o.status = 'cancelled'\n\n\n"
                      "def refund(o):\n"
                      "    return o.status == 'canceled'\n"),
    "shop/job.py": ("class Job:\n"
                    "    def __init__(self):\n"
                    "        self.running = False\n"
                    "        self.failed = False\n\n"
                    "    def go(self, ok):\n"
                    "        self.running = True\n"
                    "        if not ok:\n"
                    "            self.failed = True\n"
                    "            return\n"
                    "        self.running = False\n"),
    "shop/user.py": "class User:\n    def __init__(self, name):\n        self.name = name\n        self.kind = 'basic'\n",
    "tests/__init__.py": "",
    "tests/test_order.py": ("import unittest\nfrom shop.order import Order, pay\n\n\n"
                            "class T(unittest.TestCase):\n"
                            "    def test_pay(self):\n        o = Order()\n        pay(o)\n"
                            "        self.assertEqual(o.status, 'paid')\n\n"
                            "    def test_fixture_status(self):\n        o = Order()\n        o.status = 'weird'\n"),
}
REFUND_TEST = ("import unittest\nfrom shop.order import Order, cancel, refund\n\n\n"
               "class R(unittest.TestCase):\n"
               "    def test_refund_after_cancel(self):\n        o = Order()\n        cancel(o)\n"
               "        self.assertTrue(refund(o))\n")


def write(root, rel, text):
    p = os.path.join(root, *rel.split("/"))
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, "w", encoding="utf-8") as fh:
        fh.write(text)


def good_map():
    return {
        "machines": [
            {"name": "Order", "fields": ["status"], "initial": "new",
             "states": ["new", "paid", "cancelled"], "terminal": ["paid", "cancelled"],
             "transitions": [{"from": "new", "to": "new", "at": "shop/order.py:3"},
                             {"from": "new", "to": "paid", "at": "shop/order.py:pay"},
                             {"from": "*", "to": "cancelled", "at": "shop/order.py:cancel"}]},
            {"name": "Job", "fields": ["flags:shop/job.py:Job"], "initial": "idle",
             "states": ["idle", "running", "failed"], "terminal": [],
             "transitions": [{"from": "idle", "to": "idle", "at": "shop/job.py:Job.__init__"},
                             {"from": "*", "to": "running", "at": "shop/job.py:go"}]},
        ],
        "dismissed": [],
        "findings": [
            {"kind": "bug", "machine": "Order", "what": "refund checks 'canceled', cancel writes 'cancelled'",
             "covers": ["value:status=canceled"], "test": "python -m unittest tests.test_refund", "fixed": True},
        ],
    }


def fix_refund(root):
    write(root, "tests/test_refund.py", REFUND_TEST)
    path = os.path.join(root, "shop", "order.py")
    with open(path, encoding="utf-8") as fh:
        text = fh.read()
    write(root, "shop/order.py", text.replace("'canceled'", "'cancelled'"))


class Repo(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.root = os.path.join(self._tmp.name, "repo")
        for rel, text in FILES.items():
            write(self.root, rel, text)

    def s(self, *args):
        return run("states.py", self.root, *args)

    def record(self):
        code, out, err = self.s("--run", TESTS)
        self.assertEqual(code, 0, out + err)
        return out

    def map(self, m):
        write(self.root, ".states/machines.json", json.dumps(m))

    def done(self):
        return self.s("--done")

    def refused(self, needle):
        code, out, err = self.done()
        self.assertEqual(code, 1, out + err)
        self.assertIn("STATES: refused", out)
        self.assertIn(needle, out)
        return out


class Find(Repo):
    def test_a_string_field_lists_every_write_and_check(self):
        out = self.s()[1]
        self.assertIn("## field:status", out)
        for spot in ("shop/order.py:3 (Order.__init__)", "shop/order.py:9 (pay)", "shop/order.py:13 (cancel)"):
            self.assertIn(spot, out)
        self.assertIn("shop/order.py:7 (pay) == 'new'", out)

    def test_a_value_checked_but_never_set_is_marked(self):
        out = self.s()[1]
        self.assertIn("checked but never set: canceled", out)
        self.assertIn("value:status=canceled", out)

    def test_flags_of_one_class_are_a_group_with_their_combinations(self):
        out = self.s()[1]
        self.assertIn("## flags:shop/job.py:Job", out)
        self.assertIn("failed, running (4 combinations", out)

    def test_a_field_written_once_is_not_a_candidate(self):
        self.assertNotIn("field:kind", self.s()[1])

    def test_test_files_are_not_scanned(self):
        self.assertNotIn("tests/test_order.py", self.s()[1])

    def test_js_writes_and_checks_are_read(self):
        write(self.root, "web/cart.js", "function open(c) {\n  c.phase = 'open';\n}\n"
                                        "function close(c) {\n  c.phase = 'closed';\n  if (c.phase === 'shut') {}\n}\n")
        out = self.s()[1]
        self.assertIn("## field:phase", out)
        self.assertIn("web/cart.js:2 (open)", out)
        self.assertIn("checked but never set: shut", out)

    def test_candidates_file_is_written(self):
        self.s()
        self.assertTrue(os.path.exists(os.path.join(self.root, ".states", "candidates.md")))


class Record(Repo):
    def test_a_command_with_no_countable_tests_is_refused(self):
        code, out, _ = self.s("--run", "python -c \"print(1)\"")
        self.assertEqual(code, 1)
        self.assertIn("ran no tests", out)
        self.assertFalse(os.path.exists(os.path.join(self.root, ".states", "record.json")))

    def test_the_tree_as_it_was_is_copied(self):
        self.record()
        self.assertTrue(os.path.exists(os.path.join(self.root, ".states", "before", "shop", "order.py")))

    def test_done_without_a_record_is_refused(self):
        code, out, _ = self.done()
        self.assertEqual(code, 1)
        self.assertIn("no record", out)


class Done(Repo):
    def setUp(self):
        super().setUp()
        self.record()
        fix_refund(self.root)

    def test_a_complete_map_with_a_proven_fix_is_done(self):
        self.map(good_map())
        code, out, err = self.done()
        self.assertEqual(code, 0, out + err)
        self.assertIn("STATES: done", out)
        with open(os.path.join(self.root, ".states", "MACHINES.md"), encoding="utf-8") as fh:
            md = fh.read()
        self.assertIn("stateDiagram-v2", md)
        self.assertIn("new --> paid: pay", md)
        self.assertIn("bug, fixed", md)

    def test_an_unmapped_candidate_is_refused(self):
        m = good_map()
        del m["machines"][1]
        self.map(m)
        self.refused("flags:shop/job.py:Job is in no machine and not dismissed")

    def test_a_dismissal_needs_a_reason(self):
        m = good_map()
        del m["machines"][1]
        m["dismissed"] = [{"candidate": "flags:shop/job.py:Job", "why": ""}]
        self.map(m)
        self.refused("with no reason")

    def test_a_dismissal_with_a_reason_is_accepted(self):
        m = good_map()
        del m["machines"][1]
        m["dismissed"] = [{"candidate": "flags:shop/job.py:Job", "why": "two independent switches"}]
        self.map(m)
        self.assertEqual(self.done()[0], 0)

    def test_a_write_in_no_transition_is_refused(self):
        m = good_map()
        m["machines"][0]["transitions"].pop(2)
        self.map(m)
        self.refused("the write at shop/order.py:13 (cancel)")

    def test_also_needs_a_why_and_then_covers_the_write(self):
        m = good_map()
        m["machines"][0]["transitions"].pop(2)
        m["machines"][0]["also"] = [{"at": "shop/order.py:cancel", "why": ""}]
        self.map(m)
        self.refused("has no why")
        m["machines"][0]["also"][0]["why"] = "admin override"
        self.map(m)
        self.assertEqual(self.done()[0], 0)

    def test_a_constructor_literal_needs_no_transition(self):
        m = good_map()
        m["machines"][0]["transitions"].pop(0)
        m["machines"][1]["transitions"].pop(0)
        self.map(m)
        code, out, err = self.done()
        self.assertEqual(code, 0, out + err)

    def test_a_written_value_that_is_not_a_state_is_refused(self):
        m = good_map()
        m["machines"][0]["states"].remove("cancelled")
        m["machines"][0]["terminal"].remove("cancelled")
        m["machines"][0]["transitions"].pop(2)
        m["machines"][0]["also"] = [{"at": "shop/order.py:cancel", "why": "x"}]
        self.map(m)
        self.refused("set to 'cancelled' but that is not one of its states")

    def test_a_value_checked_but_never_set_needs_a_finding(self):
        m = good_map()
        m["findings"] = []
        self.map(m)
        self.refused("no finding covers value:status=canceled")

    def test_an_ok_finding_needs_a_why(self):
        m = good_map()
        m["findings"] = [{"kind": "ok", "machine": "Order", "what": "comes from outside",
                          "covers": ["value:status=canceled"]}]
        self.map(m)
        self.refused("gives no why")

    def test_a_state_nothing_leaves_is_refused_unless_terminal_or_a_finding(self):
        m = good_map()
        m["machines"][0]["terminal"] = ["cancelled"]
        m["machines"][0]["transitions"][2]["from"] = "new"
        self.map(m)
        self.refused("nothing leaves 'paid'")
        m["findings"].append({"kind": "ok", "machine": "Order", "what": "paid is the end",
                              "covers": ["deadend:Order:paid"], "why": "paid orders are done"})
        self.map(m)
        self.assertEqual(self.done()[0], 0)

    def test_a_transition_to_an_unknown_state_is_refused(self):
        m = good_map()
        m["machines"][0]["transitions"].append({"from": "paid", "to": "shipped", "at": "shop/order.py:pay"})
        self.map(m)
        self.refused("transition to 'shipped', which is not a state")

    def test_a_transition_from_an_unknown_state_is_refused(self):
        m = good_map()
        m["machines"][0]["transitions"].append({"from": "lost", "to": "paid", "at": "shop/order.py:pay"})
        self.map(m)
        self.refused("transition from 'lost', which is not a state")

    def test_a_transition_needs_an_at(self):
        m = good_map()
        m["machines"][0]["transitions"].append({"from": "new", "to": "paid"})
        self.map(m)
        self.refused("has no `at`")

    def test_a_machine_with_no_states_is_refused(self):
        m = good_map()
        m["machines"].append({"name": "Empty", "fields": [], "states": [], "transitions": []})
        self.map(m)
        self.refused("Empty: no states")

    def test_a_finding_must_say_what(self):
        m = good_map()
        m["findings"].append({"kind": "ok", "machine": "Order", "what": " ", "covers": [], "why": "x"})
        self.map(m)
        self.refused("says nothing in `what`")

    def test_a_broken_map_file_is_refused(self):
        write(self.root, ".states/machines.json", "{not json")
        code, out, _ = self.done()
        self.assertEqual(code, 1)
        self.assertIn("not valid JSON", out)

    def test_one_field_name_can_belong_to_two_machines(self):
        write(self.root, "shop/ship.py", "class Parcel:\n    def __init__(self):\n        self.status = 'boxed'\n\n\n"
                                         "def send(p):\n    p.status = 'sent'\n")
        m = good_map()
        m["machines"].append({"name": "Parcel", "fields": ["status"], "states": ["boxed", "sent"],
                              "terminal": ["sent"],
                              "transitions": [{"from": "boxed", "to": "boxed", "at": "shop/ship.py:Parcel.__init__"},
                                              {"from": "boxed", "to": "sent", "at": "shop/ship.py:send"}]})
        self.record_again()  # the tree as it was now has the refund fixed, so no finding is owed
        m["findings"] = []
        self.map(m)
        code, out, err = self.done()
        self.assertEqual(code, 0, out + err)
        m["machines"][2]["transitions"].pop()
        self.map(m)
        self.refused("the write at shop/ship.py:7 (send)")

    def record_again(self):
        code, out, err = self.s("--run", TESTS)
        self.assertEqual(code, 0, out + err)

    def test_a_bug_needs_a_test(self):
        m = good_map()
        del m["findings"][0]["test"]
        self.map(m)
        self.refused("has no test command")

    def test_a_bug_test_that_passes_on_the_old_tree_is_refused(self):
        m = good_map()
        m["findings"][0]["test"] = "python -m unittest tests.test_order"
        self.map(m)
        self.refused("passes on the tree as it was")

    def test_a_bug_test_that_fails_on_an_import_error_is_refused(self):
        write(self.root, "tests/test_refund.py", "import shop.nothere\n")
        m = good_map()
        m["findings"][0]["fixed"] = False
        self.map(m)
        self.refused("not the bug")

    def test_a_fixed_bug_whose_test_fails_now_is_refused(self):
        with open(os.path.join(self.root, "shop", "order.py"), encoding="utf-8") as fh:
            text = fh.read()
        write(self.root, "shop/order.py", text.replace("== 'cancelled'", "== 'canceled'"))
        os.remove(os.path.join(self.root, "tests", "test_refund.py"))
        write(self.root, ".states/proofs/test_refund.py", REFUND_TEST)
        m = good_map()
        m["findings"][0]["test"] = "python -m unittest discover -s .states/proofs"
        self.map(m)
        self.refused("is marked fixed but")

    def test_an_open_bug_proven_from_proofs_is_done_and_one_that_passes_now_is_refused(self):
        with open(os.path.join(self.root, "shop", "order.py"), encoding="utf-8") as fh:
            text = fh.read()
        write(self.root, "shop/order.py", text.replace("== 'cancelled'", "== 'canceled'"))
        os.remove(os.path.join(self.root, "tests", "test_refund.py"))
        write(self.root, ".states/proofs/test_refund.py", REFUND_TEST)
        m = good_map()
        m["findings"][0].update(test="python -m unittest discover -s .states/proofs", fixed=False)
        self.map(m)
        code, out, err = self.done()
        self.assertEqual(code, 0, out + err)
        self.assertIn("1 bugs proven (0 fixed)", out)
        fix_refund(self.root)
        self.refused("is marked open but")

    def test_a_test_that_passed_and_now_fails_is_refused(self):
        write(self.root, "tests/test_order.py", FILES["tests/test_order.py"].replace("'paid')", "'nope')"))
        self.map(good_map())
        self.refused("the tests passed before and fail now")

    def test_fewer_tests_is_refused(self):
        write(self.root, "tests/test_order.py", FILES["tests/test_order.py"].split("    def test_fixture")[0])
        os.remove(os.path.join(self.root, "tests", "test_refund.py"))
        write(self.root, ".states/proofs/test_refund.py", REFUND_TEST)
        m = good_map()
        m["findings"][0]["test"] = "python -m unittest discover -s .states/proofs"
        self.map(m)
        self.refused("fewer tests ran")


class Skill(unittest.TestCase):
    def test_skill_is_short_manual_and_names_its_helper(self):
        with open(os.path.join(ROOT, "plugin", "skills", "state-machines", "SKILL.md"), encoding="utf-8") as fh:
            text = fh.read()
        head, body = text.split("---", 2)[1:]
        self.assertIn("disable-model-invocation: true", head)
        self.assertLessEqual(len(body), 3000)
        self.assertIn("scripts/states.py", body)
        self.assertIn("--done", body)
        self.assertIn(".states/proofs", body)


if __name__ == "__main__":
    unittest.main()
