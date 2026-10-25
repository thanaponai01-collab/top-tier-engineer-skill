#!/usr/bin/env python3
"""
graph-audit.py — the import/reference graph behind latent-audit.

Run them all with `python -m unittest discover tests`.
"""
import json, os, tempfile, unittest

from _helpers import run


class GraphAudit(unittest.TestCase):
    """graph-audit.py — planted-defect fixture: one upward import, one dead
    module, one unused def, one entry point that must NOT be flagged, and one
    raw-text rescue (a module referenced only from a yml is not dead)."""

    def _fixture(self, tmp, with_yml_rescue=False):
        def w(rel, text):
            p = os.path.join(tmp, rel)
            os.makedirs(os.path.dirname(p), exist_ok=True)
            open(p, "w", encoding="utf-8").write(text)
        w("main.py", 'from app.routes.orders import order_page\n'
                     'if __name__ == "__main__":\n    order_page()\n')
        w("app/routes/orders.py", "from app.services.billing import charge\n"
                                  "def order_page():\n    return charge(10)\n")
        w("app/services/billing.py",
          "from app.models.invoice import Invoice\n"
          "from app.routes.orders import order_page\n"   # upward: domain -> interface
          "def charge(amount):\n    return Invoice(amount)\n"
          "def legacy_discount(amount):\n    return amount * 0.9\n")
        w("app/models/invoice.py",
          "class Invoice:\n    def __init__(self, amount):\n"
          "        self.amount = amount\n")
        w("app/services/old_report.py",
          'def build_report():\n    return "report"\n')
        w("layers.txt", "interface: app/routes/\ndomain: app/services/\n"
                        "data: app/models/\n")
        if with_yml_rescue:
            w("tasks.yml", "report_task: app.services.old_report\n")
        return os.path.join(tmp, "layers.txt")

    def test_planted_defects_all_caught_entry_spared(self):
        with tempfile.TemporaryDirectory() as tmp:
            layers = self._fixture(tmp)
            code, out, err = run("graph-audit.py", tmp, "--layers", layers,
                                 "--json")
            self.assertEqual(code, 1, out + err)
            r = json.loads(out)
            self.assertEqual([d["module"] for d in r["dead_modules"]],
                             ["app.services.old_report"])   # main NOT flagged
            self.assertEqual(len(r["layer_breaches"]), 1, r["layer_breaches"])
            self.assertIn("domain", r["layer_breaches"][0]["edge"])
            names = {u["name"] for u in r["unused_defs"]}
            self.assertIn("legacy_discount", names)

    def test_edges_flag_writes_the_graph_for_other_tools(self):
        """--edges FILE dumps the import graph (module -> file, importer -> imported @ line)
        so arch-design's dep-map.py can read it without importing this script."""
        with tempfile.TemporaryDirectory() as tmp:
            self._fixture(tmp)
            out_file = os.path.join(tmp, "edges.json")
            code, out, err = run("graph-audit.py", tmp, "--edges", out_file)
            self.assertIn(code, (0, 1), out + err)
            g = json.load(open(out_file, encoding="utf-8"))
            self.assertIn("app.services.billing", g["modules"])
            self.assertTrue(g["modules"]["app.services.billing"].endswith("billing.py"))
            self.assertIn(
                {"from": "app.services.billing", "to": "app.models.invoice", "line": 1},
                g["edges"])

    def test_raw_text_reference_rescues_dead_candidate(self):
        with tempfile.TemporaryDirectory() as tmp:
            layers = self._fixture(tmp, with_yml_rescue=True)
            code, out, err = run("graph-audit.py", tmp, "--layers", layers,
                                 "--json")
            r = json.loads(out)
            self.assertEqual(r["dead_modules"], [], out)

    def test_verdict_line_grammar(self):
        with tempfile.TemporaryDirectory() as tmp:
            layers = self._fixture(tmp)
            code, out, _ = run("graph-audit.py", tmp, "--layers", layers)
            last = [l for l in out.splitlines() if l.startswith("LATENT:")][-1]
            self.assertIn("findings(dead: 1, unused:", last)

    def test_unmeasured_layers_are_never_folded_into_clean(self):
        """The denominator. Without --layers the layer dimension is
        not measured, so the verdict must say UNMEASURED, not `clean` and not `0`. The
        human report always said "this is a gap, not a clean result"; the verdict line
        said `clean` anyway, which is the half most readers and every grep actually see."""
        with tempfile.TemporaryDirectory() as tmp:
            open(os.path.join(tmp, "a.py"), "w").write("import b\n")
            open(os.path.join(tmp, "b.py"), "w").write("def f():\n    return 1\n")
            code, out, _ = run("graph-audit.py", tmp, "--entry", "a")
            last = [l for l in out.splitlines() if l.startswith("LATENT:")][-1]
            self.assertIn("UNMEASURED", last, out)
            self.assertNotIn("clean(", last)
            # An unmeasured dimension is a gap in the INVOCATION, not a defect in the
            # subject: it must not fail by default, or the gate goes permanently red.
            self.assertEqual(code, 0, out)

    def test_empty_tree_blocks(self):
        with tempfile.TemporaryDirectory() as tmp:
            code, out, _ = run("graph-audit.py", tmp)
            self.assertEqual(code, 2, out)
            self.assertIn("blocked(no analyzable source)", out)


def by_name_repo(tmp):
    """jobs/nightly.py is loaded only by a name read from schedule.json; old.py is really dead;
    the one unit test calls neither, so it passes with or without them."""
    def w(rel, text):
        p = os.path.join(tmp, *rel.split("/"))
        os.makedirs(os.path.dirname(p), exist_ok=True)
        with open(p, "w", encoding="utf-8") as fh:
            fh.write(text)
    w("cli.py", "import json, sys\nfrom importlib import import_module\n"
                "def main():\n"
                "    for n in json.load(open('schedule.json'))['jobs']:\n"
                "        print(import_module('jobs.' + n.replace('-', '_')).run())\n"
                "if __name__ == '__main__':\n    main()\n")
    w("schedule.json", '{"jobs": ["nightly-sum"]}\n')
    w("jobs/__init__.py", "")
    w("jobs/nightly_sum.py", "def run():\n    return 'summed'\n")
    w("old.py", "def legacy():\n    return 1\n")
    w("test_cli.py", "import unittest\nclass T(unittest.TestCase):\n"
                     "    def test_ok(self):\n        self.assertTrue(True)\n")


class TryDelete(unittest.TestCase):
    """--try-delete is the checkpoint: a deletion counts only when something that could have
    noticed it ran before and after, in a copy, and still passes."""

    def test_a_check_that_breaks_marks_the_file_live_and_the_repo_is_untouched(self):
        with tempfile.TemporaryDirectory() as tmp:
            by_name_repo(tmp)
            code, out, err = run("graph-audit.py", tmp, "--try-delete", "jobs/nightly_sum.py",
                                 "--run", "python cli.py")
            self.assertEqual(code, 1, out + err)
            self.assertIn("BREAKS", out)
            self.assertIn("No module named", out)
            self.assertIn("DELETE-CHECK: breaks(run: python cli.py)", out)
            self.assertTrue(os.path.exists(os.path.join(tmp, "jobs", "nightly_sum.py")))

    def test_green_unit_tests_alone_are_weak_not_proof(self):
        with tempfile.TemporaryDirectory() as tmp:
            by_name_repo(tmp)
            code, out, err = run("graph-audit.py", tmp, "--try-delete", "jobs/nightly_sum.py")
            self.assertEqual(code, 2, out + err)
            self.assertIn("DELETE-CHECK: weak(tests only)", out)

    def test_really_dead_code_breaks_nothing(self):
        with tempfile.TemporaryDirectory() as tmp:
            by_name_repo(tmp)
            code, out, err = run("graph-audit.py", tmp, "--try-delete", "old.py", "--run", "python cli.py")
            self.assertEqual(code, 0, out + err)
            self.assertIn("DELETE-CHECK: nothing-breaks(", out)

    def test_several_files_name_the_live_one(self):
        with tempfile.TemporaryDirectory() as tmp:
            by_name_repo(tmp)
            code, out, err = run("graph-audit.py", tmp, "--try-delete", "old.py", "jobs/nightly_sum.py",
                                 "--run", "python cli.py")
            self.assertEqual(code, 1, out + err)
            self.assertRegex(out, r"LIVE\s+jobs/nightly_sum\.py")
            self.assertRegex(out, r"ok\s+old\.py")

    def test_a_check_already_failing_proves_nothing(self):
        with tempfile.TemporaryDirectory() as tmp:
            by_name_repo(tmp)
            os.remove(os.path.join(tmp, "test_cli.py"))
            code, out, err = run("graph-audit.py", tmp, "--try-delete", "old.py",
                                 "--run", "python -c \"raise SystemExit(3)\"")
            self.assertEqual(code, 2, out + err)
            self.assertIn("already failing", out)
            self.assertIn("DELETE-CHECK: unchecked(every check was already failing)", out)

    def test_nothing_that_could_notice_is_unchecked(self):
        with tempfile.TemporaryDirectory() as tmp:
            by_name_repo(tmp)
            os.remove(os.path.join(tmp, "test_cli.py"))
            code, out, err = run("graph-audit.py", tmp, "--try-delete", "old.py")
            self.assertEqual(code, 2, out + err)
            self.assertIn("DELETE-CHECK: unchecked(nothing could notice)", out)

    def test_a_missing_path_is_blocked(self):
        with tempfile.TemporaryDirectory() as tmp:
            by_name_repo(tmp)
            code, out, _ = run("graph-audit.py", tmp, "--try-delete", "nope.py")
            self.assertEqual(code, 2, out)
            self.assertIn("DELETE-CHECK: blocked(", out)


class FeatureMapRoots(unittest.TestCase):
    """A file the repo's FEATURES.md names is live: the map recorded a way in that the import
    graph cannot see, and its recorded runs are one of --try-delete's checks."""

    def _mapped(self, tmp):
        by_name_repo(tmp)
        with open(os.path.join(tmp, "FEATURES.md"), "w", encoding="utf-8") as fh:
            fh.write("# FEATURES\n\n## Nightly\n- what: Run the scheduled jobs.\n- cli: `cli.py` @ cli.py\n"
                     "- trace: `main` @ cli.py > `run` @ jobs/nightly_sum.py\n- status: traced\n")

    def test_mapped_files_are_never_candidates(self):
        with tempfile.TemporaryDirectory() as tmp:
            self._mapped(tmp)
            code, out, err = run("graph-audit.py", tmp, "--json")
            r = json.loads(out)
            self.assertNotIn("jobs.nightly_sum", [d["module"] for d in r["dead_modules"]], out)
            self.assertIn({"file": "jobs/nightly_sum.py", "feature": "Nightly", "no_importer": True},
                          r["mapped"])
            code, out, err = run("graph-audit.py", tmp)
            self.assertRegex(out, r"jobs/nightly_sum\.py\s+\(Nightly\)\s+no import names it")
            self.assertIn("old", [d["module"] for d in r["dead_modules"]])

    def test_without_the_map_the_by_name_job_is_a_suspect(self):
        with tempfile.TemporaryDirectory() as tmp:
            by_name_repo(tmp)
            code, out, err = run("graph-audit.py", tmp, "--json")
            self.assertIn("jobs.nightly_sum", [d["module"] for d in json.loads(out)["dead_modules"]])

    def test_the_maps_recorded_runs_catch_a_live_deletion(self):
        with tempfile.TemporaryDirectory() as tmp:
            self._mapped(tmp)
            import subprocess, sys
            from _helpers import SCRIPTS
            subprocess.run([sys.executable, os.path.join(SCRIPTS["features.py"], "features.py"), "prove",
                            "--feature", "Nightly", "--entry", "cli: cli.py", "--", sys.executable, "cli.py"],
                           cwd=tmp, capture_output=True, text=True, check=True)
            self.assertTrue(os.path.isfile(os.path.join(tmp, ".features", "features.py")))
            code, out, err = run("graph-audit.py", tmp, "--try-delete", "jobs/nightly_sum.py")
            self.assertEqual(code, 1, out + err)
            self.assertIn("BREAKS                        map: recorded runs", out)


if __name__ == "__main__":
    unittest.main()


def gate_repo(tmp):
    """by_name_repo plus old_util.py, imported only by the dead old.py."""
    by_name_repo(tmp)
    with open(os.path.join(tmp, "old.py"), "w", encoding="utf-8") as fh:
        fh.write("from old_util import helper\ndef legacy():\n    return helper()\n")
    with open(os.path.join(tmp, "old_util.py"), "w", encoding="utf-8") as fh:
        fh.write("def helper():\n    return 1\n")


def write_verdicts(tmp, lines):
    os.makedirs(os.path.join(tmp, ".latent"), exist_ok=True)
    with open(os.path.join(tmp, ".latent", "verdicts.md"), "w", encoding="utf-8") as fh:
        fh.write("# Verdicts\n\n" + "".join(f"- {ln}\n" for ln in lines))


class Stages(unittest.TestCase):
    """The gate holds the cleanup to three outcomes: a snapshot of what really loads, deletions of
    only what never loaded with nothing broken, and a verdict for every suspect left."""

    def gate(self, tmp, *extra):
        return run("graph-audit.py", tmp, "--gate", *extra)

    def test_no_snapshot_opens_stage_1_and_shows_the_loaders(self):
        with tempfile.TemporaryDirectory() as tmp:
            gate_repo(tmp)
            code, out, _ = self.gate(tmp)
            self.assertEqual(code, 1, out)
            self.assertIn("no snapshot", out)
            self.assertIn("cli.py:5 builds module names at runtime", out)

    def test_the_snapshot_observes_what_loads(self):
        with tempfile.TemporaryDirectory() as tmp:
            gate_repo(tmp)
            code, out, err = run("graph-audit.py", tmp, "--snapshot", "--run", "python cli.py")
            self.assertEqual(code, 0, out + err)
            self.assertIn("1 of 3 suspects loaded (live), 2 never loaded", out)
            with open(os.path.join(tmp, ".latent", "snapshot.json"), encoding="utf-8") as fh:
                snap = json.load(fh)
            self.assertEqual(snap["loaded"]["jobs/nightly_sum.py"], "run: python cli.py")
            self.assertNotIn("old.py", snap["loaded"])

    def test_a_snapshot_that_never_runs_a_loader_is_refused(self):
        with tempfile.TemporaryDirectory() as tmp:
            gate_repo(tmp)
            run("graph-audit.py", tmp, "--snapshot", "--run", "python -c print(1)")
            code, out, _ = self.gate(tmp)
            self.assertIn("cli.py:5 builds module names at runtime, but no snapshot command made it load", out)
            self.assertIn("STAGE 1 snapshot: every loader exercised: open", out)
            write_verdicts(tmp, ["loader cli.py:5: the schedule is empty in this deployment"])
            code, out, _ = self.gate(tmp)
            self.assertIn("STAGE 1 snapshot: every loader exercised: holds", out)

    def test_deleting_what_the_snapshot_saw_load_is_refused(self):
        with tempfile.TemporaryDirectory() as tmp:
            gate_repo(tmp)
            run("graph-audit.py", tmp, "--snapshot", "--run", "python cli.py")
            os.remove(os.path.join(tmp, "jobs", "nightly_sum.py"))
            code, out, _ = self.gate(tmp)
            self.assertIn("jobs/nightly_sum.py: deleted, but the snapshot saw it loaded by run: python cli.py", out)

    def test_deleting_something_that_breaks_a_snapshot_command_is_refused(self):
        with tempfile.TemporaryDirectory() as tmp:
            gate_repo(tmp)
            with open(os.path.join(tmp, "check_old.py"), "w", encoding="utf-8") as fh:
                fh.write("import os, sys\nsys.exit(0 if os.path.exists('old_util.py') else 1)\n")
            run("graph-audit.py", tmp, "--snapshot", "--run", "python cli.py", "--run", "python check_old.py")
            os.remove(os.path.join(tmp, "old_util.py"))
            code, out, _ = self.gate(tmp)
            self.assertIn("after the deletions, run: python check_old.py fails", out)

    def test_a_snapshot_is_refused_after_deletions(self):
        with tempfile.TemporaryDirectory() as tmp:
            gate_repo(tmp)
            self.gate(tmp)
            os.remove(os.path.join(tmp, "old.py"))
            code, out, _ = run("graph-audit.py", tmp, "--snapshot", "--run", "python cli.py")
            self.assertEqual(code, 2, out)
            self.assertIn("SNAPSHOT: refused", out)

    def test_suspects_left_need_a_verdict_and_the_gate_drafts_slots(self):
        with tempfile.TemporaryDirectory() as tmp:
            gate_repo(tmp)
            code, out, _ = self.gate(tmp, "--run", "python cli.py")
            self.assertIn("2 suspect(s) the snapshot never loaded are still here", out)
            with open(os.path.join(tmp, ".latent", "verdicts.md"), encoding="utf-8") as fh:
                self.assertIn("- old.py: [[fill:", fh.read())
            write_verdicts(tmp, ["old.py: dead: the retired sync", "old_util.py: watch: vendored, kept on purpose"])
            code, out, _ = self.gate(tmp)
            self.assertEqual(code, 0, out)
            self.assertIn("LATENT-GATE: done(0 removed, 1 live, 1 dead not removed, 1 watch)", out)

    def test_the_cheap_route_is_snapshot_delete_gate(self):
        with tempfile.TemporaryDirectory() as tmp:
            gate_repo(tmp)
            self.gate(tmp, "--run", "python cli.py")
            os.remove(os.path.join(tmp, "old.py"))
            os.remove(os.path.join(tmp, "old_util.py"))
            code, out, err = self.gate(tmp)
            self.assertEqual(code, 0, out + err)
            self.assertIn("Removed (2;", out)
            self.assertIn("- jobs/nightly_sum.py: loaded by run: python cli.py", out)

    def test_a_deleted_file_another_file_names_needs_a_reason(self):
        with tempfile.TemporaryDirectory() as tmp:
            gate_repo(tmp)
            with open(os.path.join(tmp, "cron.txt"), "w", encoding="utf-8") as fh:
                fh.write("0 2 * * * python -c 'import old_util'\n")
            self.gate(tmp, "--run", "python cli.py")
            os.remove(os.path.join(tmp, "old.py"))
            os.remove(os.path.join(tmp, "old_util.py"))
            code, out, _ = self.gate(tmp)
            self.assertIn("old_util.py: deleted, but cron.txt:1 spells its name", out)
            write_verdicts(tmp, ["old_util.py: dead: cron.txt:1 is the 2023 crontab, no longer installed"])
            code, out, _ = self.gate(tmp)
            self.assertEqual(code, 0, out)

    def test_deleting_code_that_is_not_a_suspect_is_refused_without_a_receipt(self):
        with tempfile.TemporaryDirectory() as tmp:
            gate_repo(tmp)
            with open(os.path.join(tmp, "helper.py"), "w", encoding="utf-8") as fh:
                fh.write("X = 1\n")
            with open(os.path.join(tmp, "tool.py"), "w", encoding="utf-8") as fh:
                fh.write("import helper\nif __name__ == '__main__':\n    print(helper.X)\n")
            self.gate(tmp, "--run", "python cli.py")
            os.remove(os.path.join(tmp, "helper.py"))
            code, out, _ = self.gate(tmp)
            self.assertIn("helper.py: deleted, but it was not a suspect the snapshot covered", out)


class TryDeleteVerdicts(unittest.TestCase):
    def test_try_delete_writes_the_verdicts_it_proves_and_keeps_written_ones(self):
        with tempfile.TemporaryDirectory() as tmp:
            gate_repo(tmp)
            write_verdicts(tmp, ["old.py: dead: the warehouse sync, retired in 2025"])
            code, out, _ = run("graph-audit.py", tmp, "--try-delete", "jobs/nightly_sum.py", "old.py",
                               "old_util.py", "--run", "python cli.py")
            self.assertIn("Wrote 2 proven verdict(s)", out)
            with open(os.path.join(tmp, ".latent", "verdicts.md"), encoding="utf-8") as fh:
                text = fh.read()
            self.assertIn("- jobs/nightly_sum.py: live: deleting it breaks run: python cli.py", text)
            self.assertIn("- old.py: dead: the warehouse sync, retired in 2025", text)

    def test_weak_results_write_no_verdict(self):
        with tempfile.TemporaryDirectory() as tmp:
            gate_repo(tmp)
            code, out, _ = run("graph-audit.py", tmp, "--try-delete", "old.py")
            self.assertNotIn("Wrote", out)
