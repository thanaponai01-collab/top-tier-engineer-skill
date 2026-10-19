"""Shared CLI-invocation helper for tests/test_*.py.

Run everything with: python -m unittest discover tests
"""
import subprocess, sys, os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPTS = {
    "verify.py": os.path.join(ROOT, "plugin", "skills", "verify-loop", "scripts"),
    "compliance.py": os.path.join(ROOT, "plugin", "skills", "verify-loop", "scripts"),
}


def run(tool, *args, stdin=None):
    """Invoke a tool through its CLI; return (returncode, stdout, stderr)."""
    p = subprocess.run(
        [sys.executable, os.path.join(SCRIPTS[tool], tool), *args],
        input=stdin, capture_output=True, text=True, encoding="utf-8",
    )
    return p.returncode, p.stdout, p.stderr
