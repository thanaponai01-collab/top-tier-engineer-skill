#!/usr/bin/env python3
"""
test_tools — the suite's tools gate their own correctness.

correctness-gate demands proof over plausibility; the tools that enforce it shipped
with zero tests and had already regressed twice (a UTF-8 crash, a false-fix
classification). These are the smallest tests that fail if either returns.

One module per tool in tools/tests/test_<tool>.py. This file is the single
stdlib-only entry point: `python3 tools/test_tools.py`.
"""
import os, sys, unittest

HERE = os.path.dirname(os.path.abspath(__file__))

if __name__ == "__main__":
    tests = os.path.join(HERE, "tests")
    # The test modules import `_helpers` as a top-level name, so tests/ must be
    # importable in its own right — discover()'s top_level_dir does exactly that.
    suite = unittest.defaultTestLoader.discover(
        tests, pattern="test_*.py", top_level_dir=tests)
    result = unittest.TextTestRunner(verbosity=1).run(suite)
    sys.exit(0 if result.wasSuccessful() else 1)
