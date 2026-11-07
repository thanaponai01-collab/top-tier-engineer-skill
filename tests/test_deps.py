"""deps.py - the findings it lists, the acceptance it records, and the done check that refuses.

Each test plants the thing a rule exists to catch, so disabling that rule turns it red. Holes come
from a fixed advisories file and the date is fixed, so nothing here touches the network.
Run them all with `python -m unittest discover tests`.
"""
import json, os, re, tempfile, unittest

from _helpers import ROOT, run

TESTS = "python -m unittest discover -s tests -t ."
TODAY = "2026-11-08"
ADVISORIES = {
    "holes": [
        {"ecosystem": "PyPI", "name": "urllib3", "below": "1.26.18", "id": "CVE-2023-45803"},
        {"ecosystem": "PyPI", "name": "PyYAML", "below": "5.4", "id": "CVE-2020-14343"},
        {"ecosystem": "npm", "name": "lodash", "below": "4.17.21", "id": "CVE-2021-23337"},
    ],
    "eol": {"python": {"3.12": "2026-12-31"}},
}
FILES = {
    "requirements.in": ("requests>=2.31\nPyYAML>=5.3\nclick>=8.1\nsimplejson\ntzdata\ngunicorn\n"
                        "# pinned: the report templates need the old API\nJinja2==2.11.3\nattrs==23.1.0\n"),
    "requirements.txt": ("requests==2.32.4\n    # via -r requirements.in\nurllib3==1.24.1\n    # via requests\n"
                         "pyyaml==5.3.1\n    # via -r requirements.in\nsimplejson==3.19.2\ntzdata==2024.1\n"
                         "gunicorn==23.0.0\njinja2==2.11.3\nattrs==23.1.0\n"),
    "Dockerfile": "FROM python:3.7-slim\nCMD [\"gunicorn\", \"app.web:app\"]\n",
    ".python-version": "3.12\n",
    "app/__init__.py": "",
    "app/web.py": ("import requests, yaml, click, jinja2, attr\nfrom zoneinfo import ZoneInfo\n\n\n"
                   "def tz():\n    return ZoneInfo('UTC')\n\n\ndef add(a, b):\n    return a + b\n"),
    "web/package.json": json.dumps({"dependencies": {"lodash": "^4.17.0", "left-pad": "^1.3.0", "chalk": "^5.0.0", "serve": "^14.0.0"},
                                    "devDependencies": {"eslint": "^8.0.0"},
                                    "scripts": {"lint": "eslint src", "start": "serve dist"}}),
    "web/package-lock.json": json.dumps({"lockfileVersion": 3, "packages": {
        "": {}, "node_modules/lodash": {"version": "4.17.15"}, "node_modules/left-pad": {"version": "1.3.0"},
        "node_modules/eslint": {"version": "8.57.0"}, "node_modules/serve": {"version": "14.2.1"}}}),
    "web/src/index.js": "const _ = require('lodash');\nimport pad from 'left-pad';\n",
    "go.mod": "module example.com/x\n",
    "tests/__init__.py": "",
    "tests/test_app.py": ("import unittest\nfrom app.web import add\n\n\nclass T(unittest.TestCase):\n"
                          "    def test_add(self):\n        self.assertEqual(add(1, 2), 3)\n"
                          "    def test_add_neg(self):\n        self.assertEqual(add(-1, 1), 0)\n"),
}


def write(root, rel, text):
    p = os.path.join(root, *rel.split("/"))
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, "w", encoding="utf-8") as fh:
        fh.write(text)


def edit(root, rel, old, new):
    p = os.path.join(root, *rel.split("/"))
    with open(p, encoding="utf-8") as fh:
        text = fh.read()
    assert old in text, (rel, old)
    write(root, rel, text.replace(old, new))


class Repo(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.root = os.path.join(self._tmp.name, "repo")
        for rel, text in FILES.items():
            write(self.root, rel, text)
        self.adv = os.path.join(self._tmp.name, "advisories.json")
        write(self._tmp.name, "advisories.json", json.dumps(ADVISORIES))

    def d(self, *args, advisories=True):
        extra = ["--advisories", self.adv] if advisories else ["--offline"]
        return run("deps.py", self.root, *args, *extra, "--today", TODAY)

    def findings(self, advisories=True):
        code, out, err = self.d(advisories=advisories)
        self.assertEqual(code, 0, err)
        return out

    def line(self, out, fid):
        m = re.search(r"^- \[(high|low)\] `%s` (.*)$" % re.escape(fid), out, re.M)
        self.assertTrue(m, f"no finding {fid}:\n{out}")
        return m.group(1), m.group(2)


class Find(Repo):
    def test_an_indirect_hole_is_named_with_what_pulls_it_in(self):
        sev, text = self.line(self.findings(), "known-hole:urllib3")
        self.assertEqual(sev, "high")
        self.assertIn("1.24.1", text)
        self.assertIn("via requests", text)
        self.assertIn("CVE-2023-45803", text)

    def test_a_direct_hole_matches_the_normalized_name(self):
        _, text = self.line(self.findings(), "known-hole:pyyaml")
        self.assertIn("direct", text)

    def test_a_fixed_version_is_not_a_hole(self):
        edit(self.root, "requirements.txt", "urllib3==1.24.1", "urllib3==1.26.20")
        self.assertNotIn("known-hole:urllib3", self.findings())

    def test_a_package_missing_from_the_lock_is_drift(self):
        sev, text = self.line(self.findings(), "lock-drift:click")
        self.assertEqual(sev, "high")
        self.assertIn("requirements.txt", text)

    def test_a_pin_the_manifest_does_not_allow_is_drift(self):
        edit(self.root, "requirements.in", "PyYAML>=5.3", "PyYAML>=6.0")
        _, text = self.line(self.findings(), "lock-drift:pyyaml")
        self.assertIn("does not allow", text)

    def test_a_package_nothing_imports_is_unused(self):
        sev, _ = self.line(self.findings(), "unused:simplejson")
        self.assertEqual(sev, "low")

    def test_packages_used_without_an_import_are_not_called_unused(self):
        out = self.findings()
        for name, why in (("tzdata", "zoneinfo"), ("gunicorn", "Dockerfile")):
            self.assertNotIn(f"unused:{name}", out)
            self.assertIn(why, self.line(out, f"used-without-import:{name}")[1])

    def test_imported_names_that_differ_from_the_package_are_used(self):
        out = self.findings()
        for name in ("pyyaml", "attrs", "jinja2", "requests", "click"):
            self.assertNotIn(f"unused:{name}", out)

    def test_an_end_of_life_runtime_is_high_and_a_soon_one_is_low(self):
        out = self.findings()
        sev, text = self.line(out, "eol-runtime:python-3.7")
        self.assertEqual(sev, "high")
        self.assertIn("Dockerfile", text)
        self.assertEqual(self.line(out, "eol-soon:python-3.12")[0], "low")

    def test_an_exact_pin_without_a_reason_is_noted_and_one_with_a_reason_is_not(self):
        out = self.findings()
        self.assertEqual(self.line(out, "pinned-no-reason:attrs")[0], "low")
        self.assertNotIn("pinned-no-reason:jinja2", out)

    def test_node_holes_drift_and_unused(self):
        out = self.findings()
        self.assertIn("4.17.15", self.line(out, "known-hole:lodash")[1])
        self.assertIn("package-lock.json", self.line(out, "lock-drift:chalk")[1])
        self.assertEqual(self.line(out, "unused:chalk")[0], "low")
        self.assertNotIn("unused:left-pad", out)
        self.assertNotIn("unused:serve", out, "a package a script runs is used")

    def test_a_node_lock_outside_the_range_is_drift(self):
        edit(self.root, "web/package-lock.json", '"version": "1.3.0"', '"version": "2.0.0"')
        self.assertIn("does not allow", self.line(self.findings(), "lock-drift:left-pad")[1])

    def test_high_findings_come_first(self):
        sevs = re.findall(r"^- \[(high|low)\]", self.findings(), re.M)
        self.assertEqual(sevs, sorted(sevs, key=lambda s: s != "high"))

    def test_holes_not_checked_are_said_and_never_reported_clean(self):
        out = self.findings(advisories=False)
        self.assertNotIn("known-hole:", out)
        notes = out.split("## Not checked", 1)[1]
        self.assertIn("requirements.txt (Python): known holes not checked", notes)
        self.assertIn("(Node): known holes not checked", notes)

    def test_an_ecosystem_the_helper_cannot_read_is_listed(self):
        self.assertIn("go.mod: Go dependencies are not read", self.findings())

    def test_findings_are_written_to_the_state_folder(self):
        self.findings()
        with open(os.path.join(self.root, ".deps", "findings.md"), encoding="utf-8") as fh:
            self.assertIn("known-hole:urllib3", fh.read())


class Accept(Repo):
    def setUp(self):
        super().setUp()
        self.findings()

    def test_an_acceptance_needs_a_reason(self):
        code, out, _ = self.d("--accept", "known-hole:pyyaml", "--until", "2027-01-01")
        self.assertEqual(code, 1)
        self.assertIn("--reason", out)

    def test_an_acceptance_needs_a_future_date(self):
        for until in ("soon", "2026-01-01"):
            code, out, _ = self.d("--accept", "known-hole:pyyaml", "--reason", "x", "--until", until)
            self.assertEqual(code, 1, until)
        self.assertFalse(os.path.exists(os.path.join(self.root, ".deps", "accepted.json")))

    def test_only_a_current_finding_can_be_accepted(self):
        code, out, _ = self.d("--accept", "known-hole:nope", "--reason", "x", "--until", "2027-01-01")
        self.assertEqual(code, 1)
        self.assertIn("not a current finding", out)

    def test_an_accepted_finding_shows_its_reason(self):
        code, out, _ = self.d("--accept", "known-hole:pyyaml", "--reason", "safe_load only", "--until", "2027-01-01")
        self.assertEqual(code, 0, out)
        self.assertIn("accepted until 2027-01-01: safe_load only", self.line(self.findings(), "known-hole:pyyaml")[1])


class Baseline(Repo):
    def test_a_command_that_ran_no_tests_records_nothing(self):
        code, out, _ = self.d("--run", "python -c \"print('hi')\"")
        self.assertEqual(code, 1)
        self.assertIn("ran no tests", out)
        self.assertFalse(os.path.exists(os.path.join(self.root, ".deps", "baseline.json")))

    def test_done_without_a_baseline_is_refused(self):
        code, out, _ = self.d("--done")
        self.assertEqual(code, 1)
        self.assertIn("no baseline", out)


class Done(Repo):
    def setUp(self):
        super().setUp()
        code, out, err = self.d("--run", TESTS)
        self.assertEqual(code, 0, out + err)

    def fix_all(self):
        edit(self.root, "requirements.txt", "urllib3==1.24.1", "urllib3==1.26.20")
        edit(self.root, "requirements.txt", "pyyaml==5.3.1", "pyyaml==6.0.2")
        edit(self.root, "requirements.txt", "attrs==23.1.0", "attrs==23.1.0\nclick==8.1.7")
        edit(self.root, "Dockerfile", "python:3.7-slim", "python:3.12-slim")
        edit(self.root, "web/package-lock.json", '"version": "4.17.15"', '"version": "4.17.21"')
        edit(self.root, "web/package-lock.json", '"node_modules/eslint"', '"node_modules/chalk": {"version": "5.3.0"}, "node_modules/eslint"')

    def test_an_undecided_high_finding_is_refused(self):
        code, out, _ = self.d("--done")
        self.assertEqual(code, 1)
        self.assertIn("DEPS: not done", out)
        self.assertIn("undecided [known-hole] urllib3", out)
        self.assertIn("--accept known-hole:urllib3", out)

    def test_fixed_or_accepted_highs_are_done_and_recorded(self):
        self.fix_all()
        self.d()
        code, out, _ = self.d("--accept", "known-hole:pyyaml", "--reason", "r", "--until", "2027-01-01")
        code, out, _ = self.d("--done")
        self.assertEqual(code, 0, out)
        self.assertIn("DEPS: done", out)
        with open(os.path.join(self.root, ".deps", "history.json"), encoding="utf-8") as fh:
            hist = json.load(fh)
        self.assertIn("unused:simplejson", hist[-1]["left"])
        self.assertFalse(os.path.exists(os.path.join(self.root, ".deps", "baseline.json")))

    def test_an_accepted_high_counts_as_decided(self):
        self.fix_all()
        edit(self.root, "requirements.txt", "urllib3==1.26.20", "urllib3==1.24.1")
        self.d()
        self.d("--accept", "known-hole:urllib3", "--reason", "pinned by the vendor image", "--until", "2027-01-01")
        code, out, _ = self.d("--done")
        self.assertEqual(code, 0, out)

    def test_a_test_that_passed_and_now_fails_is_refused(self):
        self.fix_all()
        edit(self.root, "app/web.py", "return a + b", "return a - b")
        code, out, _ = self.d("--done")
        self.assertEqual(code, 1)
        self.assertIn("passed before and fail now", out)

    def test_fewer_tests_is_refused(self):
        self.fix_all()
        edit(self.root, "tests/test_app.py", "    def test_add_neg(self):\n        self.assertEqual(add(-1, 1), 0)\n", "")
        code, out, _ = self.d("--done")
        self.assertEqual(code, 1)
        self.assertIn("1 tests ran, 2 before", out)

    def test_a_manifest_changed_without_its_lock_is_refused(self):
        edit(self.root, "requirements.in", "simplejson\n", "")
        code, out, _ = self.d("--done")
        self.assertEqual(code, 1)
        self.assertIn("requirements.in changed but requirements.txt did not", out)

    def test_nothing_is_recorded_while_refused(self):
        self.d("--done")
        self.assertFalse(os.path.exists(os.path.join(self.root, ".deps", "history.json")))
        self.assertTrue(os.path.exists(os.path.join(self.root, ".deps", "baseline.json")))


class SinceLast(Repo):
    def finish(self):
        Done.fix_all(self)
        edit(self.root, "requirements.txt", "pyyaml==6.0.2", "pyyaml==5.3.1")
        self.d()
        self.d("--accept", "known-hole:pyyaml", "--reason", "safe_load only", "--until", "2026-12-01")
        code, out, _ = self.d("--done")
        self.assertEqual(code, 0, out)

    def test_the_next_run_shows_what_is_new(self):
        self.d("--run", TESTS)
        self.finish()
        edit(self.root, "requirements.txt", "urllib3==1.26.20", "urllib3==1.24.1")
        head = self.findings().split("- [", 1)[0]
        self.assertIn("new: [high] known-hole:urllib3", head)
        self.assertNotIn("simplejson", head, "a finding left last time is not new")

    def test_an_acceptance_past_its_date_is_due_again_and_blocks_done(self):
        self.d("--run", TESTS)
        self.finish()
        code, out, _ = run("deps.py", self.root, "--advisories", self.adv, "--today", "2026-12-15")
        self.assertIn("due again: known-hole:pyyaml", out)
        run("deps.py", self.root, "--advisories", self.adv, "--run", TESTS, "--today", "2026-12-15")
        code, out, _ = run("deps.py", self.root, "--done", "--advisories", self.adv, "--today", "2026-12-15")
        self.assertEqual(code, 1)
        self.assertIn("undecided [known-hole] pyyaml", out)

    def test_no_record_means_no_since_section(self):
        self.assertNotIn("Since the", self.findings())


class Skill(unittest.TestCase):
    def test_skill_is_short_manual_and_names_its_helper(self):
        with open(os.path.join(ROOT, "plugin", "skills", "dependency-health", "SKILL.md"), encoding="utf-8") as fh:
            text = fh.read()
        head, body = text.split("---", 2)[1:]
        self.assertIn("disable-model-invocation: true", head)
        self.assertLessEqual(len(body), 3000)
        for word in ("scripts/deps.py", "--done", "--accept", "Not checked"):
            self.assertIn(word, body)


if __name__ == "__main__":
    unittest.main()
