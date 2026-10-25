#!/usr/bin/env python3
"""
threat.py - the doors, the attacks and the hold stage behind threat-model.

Each test plants the thing a guard exists to catch, so disabling that part of the gate turns it red.
Run them all with `python -m unittest discover tests`.
"""
import json, os, tempfile, unittest

from _helpers import run

APP = {
    "app.py": ("import shop\n\n\ndef r_health(user, arg):\n    return 'ok'\n\n\n"
               "def r_refund(user, arg):\n    return shop.refund(user, int(arg))\n\n\n"
               "ROUTES = {'health': r_health, 'refund': r_refund}\n\n\n"
               "def handle(path, user, arg=''):\n    try:\n        return 200, ROUTES[path](user, arg)\n"
               "    except PermissionError:\n        return 403, 'no'\n"),
    "shop.py": ("CREDIT = {'bob': 0}\n\n\ndef refund(user, amount):\n    if user != 'staff':\n"
                "        raise PermissionError('staff only')\n    CREDIT['bob'] += amount\n    return CREDIT['bob']\n"),
    "tests/test_app.py": ("import unittest\nimport app\n\n\nclass T(unittest.TestCase):\n"
                          "    def test_health(self):\n        self.assertEqual(app.handle('health', 'bob')[0], 200)\n"),
}
ATTACK = ("import unittest\nimport app\n\n\nclass Refund(unittest.TestCase):\n"
          "    def test_customer_cannot_refund(self):\n        self.assertEqual(app.handle('refund', 'bob', '5')[0], 403)\n")
CMD = "python -m unittest tests.test_attacks"
REFUND = ["--attack", CMD, "--door", "app.py::r_refund", "--gets", "a customer refunds himself"]
OPEN_GUARD = ("    if user != 'staff':\n        raise PermissionError('staff only')\n", "")


def make(tmp, files=APP):
    for rel, text in files.items():
        p = os.path.join(tmp, *rel.split("/"))
        os.makedirs(os.path.dirname(p), exist_ok=True)
        with open(p, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(text)


def edit(tmp, rel, old, new):
    p = os.path.join(tmp, *rel.split("/"))
    with open(p, encoding="utf-8") as fh:
        text = fh.read()
    assert old in text, (rel, old)
    with open(p, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(text.replace(old, new))


def ledger(tmp):
    with open(os.path.join(tmp, ".threat", "state.json"), encoding="utf-8") as fh:
        return json.load(fh)


def note(tmp, door, reason):
    p = os.path.join(tmp, ".threat", "doors.md")
    with open(p, encoding="utf-8") as fh:
        lines = [f"- {door}: out: {reason}" if ln.startswith(f"- {door}:") else ln for ln in fh.read().splitlines()]
    with open(p, "w", encoding="utf-8", newline="\n") as fh:
        fh.write("\n".join(lines) + "\n")


def gate(tmp):
    code, out, err = run("threat.py", tmp, "--gate")
    return code, out + err


def opened(tmp):
    """The app with the refund guard taken out and an attack recorded on it."""
    make(tmp)
    edit(tmp, "shop.py", *OPEN_GUARD)
    make(tmp, {"tests/test_attacks.py": ATTACK})
    code, out, _ = run("threat.py", tmp, *REFUND)
    assert code == 0, out


def accounted(tmp):
    gate(tmp)
    note(tmp, "app.py::r_health", "returns a fixed string, no input and no state")


class Doors(unittest.TestCase):
    def test_route_tables_decorators_handlers_and_scripts_are_doors(self):
        with tempfile.TemporaryDirectory() as tmp:
            make(tmp, {
                "app.py": APP["app.py"] + "\n\nif __name__ == '__main__':\n    print(handle('health', 'x'))\n",
                "api.py": ("import functools\n\n\ndef route(p):\n    return lambda f: f\n\n\n@route('/x')\n"
                           "def x_view():\n    pass\n\n\n@functools.lru_cache(maxsize=4)\ndef cached():\n    pass\n\n\n"
                           "class H:\n    def do_POST(self):\n        pass\n\n    @property\n    def p(self):\n"
                           "        return 1\n"),
                "cli.py": ("import argparse\n\n\ndef cmd_wipe(a):\n    pass\n\n\np = argparse.ArgumentParser()\n"
                           "p.add_subparsers().add_parser('wipe').set_defaults(func=cmd_wipe)\n"),
                "web/page.js": "fetch('/x')\n",
                "tests/test_app.py": APP["tests/test_app.py"],
            })
            code, out, _ = run("threat.py", tmp)
            self.assertEqual(code, 0)
            for door in ("app.py::r_health", "app.py::r_refund", "app.py::__main__", "api.py::x_view",
                         "api.py::H.do_POST", "cli.py::cmd_wipe"):
                self.assertIn(door, out)
            for not_door in ("api.py::cached", "api.py::H.p", "test_health", "api.py::route"):
                self.assertNotIn(not_door, out)
            self.assertIn("no parser here for 1 files: web/page.js", out)

    def test_a_file_no_parser_reads_is_a_door_to_account_for(self):
        with tempfile.TemporaryDirectory() as tmp:
            make(tmp, dict(APP, **{"web/page.js": "fetch('/x')\n"}))
            self.assertIn("web/page.js (no parser here", gate(tmp)[1])


class Attack(unittest.TestCase):
    def test_an_abuse_that_works_is_recorded_open(self):
        with tempfile.TemporaryDirectory() as tmp:
            opened(tmp)
            a = ledger(tmp)["attacks"][0]
            self.assertEqual((a["status"], a["doors"], a["files"]), ("open", ["app.py::r_refund"], ["tests/test_attacks.py"]))
            self.assertTrue(os.path.isfile(os.path.join(tmp, ".threat", "before", "shop.py")))

    def test_an_abuse_that_is_refused_is_recorded_held(self):
        with tempfile.TemporaryDirectory() as tmp:
            make(tmp, dict(APP, **{"tests/test_attacks.py": ATTACK}))
            code, out, _ = run("threat.py", tmp, *REFUND)
            self.assertEqual(code, 0, out)
            self.assertIn("HELD", out)

    def test_an_attack_that_never_enters_its_door_proves_nothing(self):
        with tempfile.TemporaryDirectory() as tmp:
            make(tmp, dict(APP, **{"tests/test_attacks.py": ATTACK}))
            code, out, _ = run("threat.py", tmp, "--attack", CMD, "--door", "app.py::r_health", "--gets", "x")
            self.assertEqual(code, 1)
            self.assertIn("never entered app.py::r_health", out)
            self.assertFalse(ledger(tmp).get("attacks"))

    def test_an_attack_kept_outside_the_repo_is_refused(self):
        with tempfile.TemporaryDirectory() as tmp, tempfile.TemporaryDirectory() as elsewhere:
            make(tmp)
            outside = os.path.join(elsewhere, "test_probe.py").replace("\\", "/")
            make(elsewhere, {"test_probe.py": ATTACK})
            code, out, _ = run("threat.py", tmp, "--attack", f"python {outside}", "--door", "app.py::r_refund",
                               "--gets", "x")
            self.assertEqual(code, 2)
            self.assertIn("outside the repo", out)

    def test_a_whole_suite_run_is_not_an_attack(self):
        with tempfile.TemporaryDirectory() as tmp:
            make(tmp, dict(APP, **{"tests/test_attacks.py": ATTACK}))
            code, out, _ = run("threat.py", tmp, "--attack", "python -m unittest discover tests",
                               "--door", "app.py::r_refund", "--gets", "x")
            self.assertEqual(code, 2)
            self.assertIn("names no test file", out)

    def test_an_attack_the_suite_does_not_run_is_refused(self):
        with tempfile.TemporaryDirectory() as tmp:
            make(tmp, dict(APP, **{"probes/attack.py": ATTACK}))
            code, out, _ = run("threat.py", tmp, "--attack", "python -m unittest probes.attack",
                               "--door", "app.py::r_refund", "--gets", "x")
            self.assertEqual(code, 2)
            self.assertIn("not a file the project's test run picks up", out)

    def test_a_crash_is_not_a_finding(self):
        with tempfile.TemporaryDirectory() as tmp:
            make(tmp, dict(APP, **{"tests/test_attacks.py": ATTACK.replace("'5'", "'five'")}))
            code, out, _ = run("threat.py", tmp, *REFUND)
            self.assertEqual(code, 1)
            self.assertIn("errored instead of failing an assertion", out)
            self.assertFalse(ledger(tmp).get("attacks"))

    def test_an_attack_that_runs_no_tests_is_refused(self):
        with tempfile.TemporaryDirectory() as tmp:
            make(tmp, dict(APP, **{"tests/test_attacks.py": "import app\napp.handle('refund', 'bob', '5')\n"}))
            code, out, _ = run("threat.py", tmp, *REFUND)
            self.assertEqual(code, 1)
            self.assertIn("ran no tests", out)


class Account(unittest.TestCase):
    def test_nothing_attacked_keeps_stage_two_open_and_appends_the_slots(self):
        with tempfile.TemporaryDirectory() as tmp:
            make(tmp)
            code, out = gate(tmp)
            self.assertEqual(code, 1)
            self.assertIn("STAGE 2 attack: every door attacked or accounted for: open", out)
            self.assertIn("no attack recorded", out)
            with open(os.path.join(tmp, ".threat", "doors.md"), encoding="utf-8") as fh:
                self.assertIn("- app.py::r_refund: [[fill", fh.read())

    def test_a_door_out_of_reach_by_a_defense_must_be_attacked(self):
        with tempfile.TemporaryDirectory() as tmp:
            opened(tmp)
            gate(tmp)
            note(tmp, "app.py::r_health", "the role check guards it, so it is fine")
            self.assertIn("leans on a defense", gate(tmp)[1])

    def test_a_bare_out_says_too_little(self):
        with tempfile.TemporaryDirectory() as tmp:
            opened(tmp)
            gate(tmp)
            note(tmp, "app.py::r_health", "tbd")
            self.assertIn("says too little", gate(tmp)[1])

    def test_a_note_for_a_door_that_is_gone_must_go(self):
        with tempfile.TemporaryDirectory() as tmp:
            opened(tmp)
            accounted(tmp)
            with open(os.path.join(tmp, ".threat", "doors.md"), "a", encoding="utf-8") as fh:
                fh.write("- app.py::r_gone: out: a page that was removed last year entirely\n")
            self.assertIn("app.py::r_gone, which is not a door now", gate(tmp)[1])


class Hold(unittest.TestCase):
    def test_report_only_answer_lists_the_open_attack_and_never_says_secure(self):
        with tempfile.TemporaryDirectory() as tmp:
            opened(tmp)
            accounted(tmp)
            code, out = gate(tmp)
            self.assertEqual(code, 0, out)
            self.assertIn("Open today (1)", out)
            self.assertIn("a customer refunds himself: through app.py::r_refund", out)
            self.assertIn("Attacks kept where the suite runs them: tests/test_attacks.py", out)
            self.assertIn("THREAT-GATE: done(1 open, 0 held, 1/2 doors attacked)", out)

    def test_a_fix_that_shuts_the_door_and_is_seen_reopening_passes(self):
        with tempfile.TemporaryDirectory() as tmp:
            opened(tmp)
            accounted(tmp)
            edit(tmp, "app.py", "    return shop.refund(user, int(arg))",
                 "    if user != 'staff':\n        raise PermissionError('staff only')\n    return shop.refund(user, int(arg))")
            code, out = gate(tmp)
            self.assertEqual(code, 0, out)
            self.assertIn("fails again with app.py put back", out)
            self.assertIn("done(1 shut", out)

    def test_a_change_that_leaves_the_abuse_working_is_not_a_fix(self):
        with tempfile.TemporaryDirectory() as tmp:
            opened(tmp)
            accounted(tmp)
            edit(tmp, "shop.py", "CREDIT = {'bob': 0}", "CREDIT = {'bob': 0, 'alice': 0}")
            code, out = gate(tmp)
            self.assertEqual(code, 1)
            self.assertIn("attack 1 is still open after the change", out)

    def test_an_attack_loosened_until_it_passes_cannot_see_the_abuse(self):
        with tempfile.TemporaryDirectory() as tmp:
            opened(tmp)
            accounted(tmp)
            edit(tmp, "app.py", "    return shop.refund(user, int(arg))",
                 "    if user != 'staff':\n        raise PermissionError('staff only')\n    return shop.refund(user, int(arg))")
            edit(tmp, "tests/test_attacks.py", "self.assertEqual(app.handle('refund', 'bob', '5')[0], 403)",
                 "self.assertIn(app.handle('refund', 'bob', '5')[0], (200, 403))")
            code, out = gate(tmp)
            self.assertEqual(code, 1)
            self.assertIn("does not fail with app.py put back", out)

    def test_an_attack_that_flips_with_no_change_is_not_trusted(self):
        with tempfile.TemporaryDirectory() as tmp:
            opened(tmp)
            accounted(tmp)
            edit(tmp, "tests/test_attacks.py", "[0], 403)", "[0], 200)")
            code, out = gate(tmp)
            self.assertEqual(code, 1)
            self.assertIn("was open when recorded and is held now, with no product file changed", out)


if __name__ == "__main__":
    unittest.main()
