"""Shared CLI-invocation helper for tools/tests/test_*.py.

HERE resolves to tools/ (this file's grandparent), not tools/tests/, so every
test module reaches the tool scripts the same way test_tools.py always did.
"""
import subprocess, sys, os

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def run(tool, *args, stdin=None):
    """Invoke a tool through its CLI; return (returncode, stdout, stderr)."""
    p = subprocess.run(
        [sys.executable, os.path.join(HERE, tool), *args],
        input=stdin, capture_output=True, text=True, encoding="utf-8",
    )
    return p.returncode, p.stdout, p.stderr
