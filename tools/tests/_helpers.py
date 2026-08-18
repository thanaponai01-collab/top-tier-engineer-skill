"""Shared CLI-invocation helper for tools/tests/test_*.py.

HERE resolves to tools/ (this file's grandparent), not tools/tests/, so every
test module reaches the tool scripts the same way test_tools.py always did.
"""
import subprocess, sys, os

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Put tools/ on the path here rather than relying on the invocation to do it. Several
# tools are loaded in-process by the tests and import their own siblings by bare name
# (`from _encoding import utf8_streams`), which resolves only when tools/ is importable.
# `python3 tools/test_tools.py` supplies that as sys.path[0]; a maintainer's
# `python -m unittest discover -s tools/tests` does not, and used to fail with a
# ModuleNotFoundError that says nothing about the real cause. Every test module imports
# this one, so doing it here makes the suite invocation-independent.
if HERE not in sys.path:
    sys.path.insert(0, HERE)


def run(tool, *args, stdin=None):
    """Invoke a tool through its CLI; return (returncode, stdout, stderr)."""
    p = subprocess.run(
        [sys.executable, os.path.join(HERE, tool), *args],
        input=stdin, capture_output=True, text=True, encoding="utf-8",
    )
    return p.returncode, p.stdout, p.stderr
