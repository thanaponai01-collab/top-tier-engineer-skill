#!/usr/bin/env python3
"""
test_cadence_check — tests for cadence-check.py (PROTOCOL §12's watcher).

Kept as its own module rather than added to test_tools.py on purpose:
DEBT_LEDGER.md D-4 already flags test_tools.py at 799/800 SLoC with "no headroom
left to re-lock into ... the next test added to this file MUST pay down first
(extract, then add)". cadence-check.py is a brand-new tool with no existing tests
to extract, so its tests start here instead of pushing that file over its own
repay_at trigger. Run: `python tools/test_cadence_check.py` (stdlib unittest,
matching test_tools.py's convention); wired into the enforcement floor alongside it.
"""
import os
import subprocess
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))


def run(tool, *args, stdin=None):
    p = subprocess.run(
        [sys.executable, os.path.join(HERE, tool), *args],
        input=stdin, capture_output=True, text=True, encoding="utf-8",
    )
    return p.returncode, p.stdout, p.stderr


def _load():
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "cadence_check_under_test", os.path.join(HERE, "cadence-check.py"))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


class CadenceCheck(unittest.TestCase):
    """PROTOCOL §12's own watcher (IMPROVEMENT_PLAN.md Phase 3 / LIVE_RUN_005's `scrutinize`
    correction): the run-cadence obligation must not ship as prose nothing checks, the same
    failure F4 named for DEBT_LEDGER triggers. Tests the pure `evaluate()` logic directly
    (no git needed) plus one CLI smoke test against this repo's real history."""

    def test_pre_introduction_releases_are_never_gaps(self):
        """Rule-vintage (§11): §12 must not condemn a release that predates it, even if
        that release changed a skill body with no live run — most of this suite's own
        history did exactly that."""
        cc = _load()
        releases = [{"version": (1, 18, 0), "body_changed": True, "live_run_added": False}]
        self.assertEqual(cc.evaluate(releases, introduced_at=(1, 20, 1)), [])

    def test_skill_body_change_without_live_run_is_a_gap(self):
        cc = _load()
        releases = [{"version": (1, 21, 0), "body_changed": True, "live_run_added": False}]
        gaps = cc.evaluate(releases, introduced_at=(1, 20, 1))
        self.assertEqual(len(gaps), 1)
        self.assertEqual(gaps[0]["version"], (1, 21, 0))

    def test_skill_body_change_with_live_run_is_clean(self):
        cc = _load()
        releases = [{"version": (1, 20, 1), "body_changed": True, "live_run_added": True}]
        self.assertEqual(cc.evaluate(releases, introduced_at=(1, 20, 1)), [])

    def test_tools_only_release_needs_no_live_run(self):
        cc = _load()
        releases = [{"version": (1, 20, 2), "body_changed": False, "live_run_added": False}]
        self.assertEqual(cc.evaluate(releases, introduced_at=(1, 20, 1)), [])

    def test_unmappable_release_is_reported_not_silently_skipped(self):
        """Same discipline as run-trace.py: a stage that could not be checked is a
        finding, never a silent pass."""
        cc = _load()
        releases = [{"version": (1, 20, 1), "body_changed": None, "live_run_added": False}]
        gaps = cc.evaluate(releases, introduced_at=(1, 20, 1))
        self.assertEqual(len(gaps), 1)
        self.assertIn("unmappable", gaps[0]["reason"])

    def test_parses_changelog_versions_newest_first(self):
        cc = _load()
        text = "# Changelog\n\n## 1.20.1 — 2026-08-02 — x\n\n## 1.20.0 — 2026-08-02 — y\n"
        self.assertEqual(cc.parse_changelog_versions(text), [(1, 20, 1), (1, 20, 0)])

    def test_cli_runs_against_real_history_without_crashing(self):
        """Smoke test: the real tool against this repo's real CHANGELOG.md/.git — must
        exit 0 or 1 (a real verdict), never crash or exit 2 (blocked)."""
        code, out, err = run("cadence-check.py", "--root", os.path.dirname(HERE))
        self.assertIn(code, (0, 1), out + err)
        self.assertRegex(out, r"CADENCE: (clean|gap)\(")


if __name__ == "__main__":
    unittest.main()
