#!/usr/bin/env python3
"""
test_tools — the suite's tools gate their own correctness.

correctness-gate is a skill that demands proof over plausibility; the tools that
enforce it (verdict-lint, run-trace, structure-report) shipped with zero tests and
had already regressed twice (a UTF-8 crash, a verdict-line off-by-one, a false-fix
classification). This suite is the smallest thing that fails if any of those return.

The tests live one per tool in tools/tests/test_<tool>.py (D-4 / W-1 repayment: this
file used to carry all of them and crossed the god-file line). This file stays the
single stdlib-only entry point a director or CI runs: `python3 tools/test_tools.py`.
"""
import os, sys, unittest

HERE = os.path.dirname(os.path.abspath(__file__))

if __name__ == "__main__":
    suite = unittest.defaultTestLoader.discover(
        os.path.join(HERE, "tests"), pattern="test_*.py")
    result = unittest.TextTestRunner(verbosity=1).run(suite)
    sys.exit(0 if result.wasSuccessful() else 1)
