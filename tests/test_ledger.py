#!/usr/bin/env python3
"""
tools/ledger.py turns every retained eval run into evals/LEDGER.md. These tests hold the committed
ledger to the results and pin the rules that decide how much a row may be trusted.

Run them all with `python -m unittest discover tests`.
"""
import importlib.util
from pathlib import Path
import unittest

from _helpers import ROOT

_spec = importlib.util.spec_from_file_location("ledger", Path(ROOT) / "tools" / "ledger.py")
ledger = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(ledger)


def row(arm, passed, cost=0.1):
    return {"arm": arm, "passed": passed, "cost_usd": cost, "model": "m"}


def run(started, version, with_rows, without_rows):
    return {"started": started, "version": version, "arms": {"with": with_rows, "without": without_rows}}


class Ledger(unittest.TestCase):
    def test_committed_ledger_matches_results(self):
        text = ledger.render(*ledger.build())
        have = (Path(ROOT) / "evals" / "LEDGER.md").read_text(encoding="utf-8").replace("\r\n", "\n")
        self.assertEqual(have, text, "run python tools/ledger.py --write")

    def test_verdicts(self):
        self.assertEqual(ledger.verdict(0, 3, 3, 3), "helps")
        self.assertEqual(ledger.verdict(3, 3, 1, 3), "HURTS")
        self.assertEqual(ledger.verdict(1, 3, 2, 3), "leans helps")
        self.assertEqual(ledger.verdict(2, 2, 2, 2), "no difference")

    def test_latest_paired_run_wins_by_started_stamp_and_flags_trust(self):
        case = next(p.name for p in ledger.CASES.iterdir() if p.is_dir())
        runs = {case: {
            "z-old-name": run("2026-01-01-0000", "1.0", [row("with", True)] * 3, [row("without", False)] * 3),
            "a-contaminated": run("2026-02-01-0000", "9.9", [row("with", False)], [row("without", True)]),
            "with-only": run("2026-03-01-0000", "9.9", [row("with", True)], []),
        }}
        rows, never, _ = ledger.build(runs, current_version="9.9")
        mine = [r for r in rows if r["case"] == case][0]
        self.assertEqual(mine["run"], "a-contaminated")  # newer stamp; a one-sided run is not a pair
        self.assertIn("thin", mine["flags"])
        self.assertIn("untrusted", mine["flags"])
        self.assertEqual(mine["verdict"], "HURTS")
        self.assertNotIn(case, [c for c, _, _ in never])

    def test_unpaired_case_is_listed_not_scored(self):
        rows, never, _ = ledger.build({}, current_version="1")
        self.assertEqual(rows, [])
        self.assertTrue(never)


if __name__ == "__main__":
    unittest.main()
