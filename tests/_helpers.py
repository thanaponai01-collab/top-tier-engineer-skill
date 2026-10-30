"""Shared CLI-invocation helper for tests/test_*.py.

Run everything with: python -m unittest discover tests
"""
import subprocess, sys, os

# Windows putenv limit guard: prevent patch.dict(os.environ) from failing on oversized external vars
for _k, _v in list(os.environ.items()):
    if len(_v) > 30000:
        del os.environ[_k]

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPTS = {
    "verify.py": os.path.join(ROOT, "plugin", "skills", "verify-loop", "scripts"),
    "compliance.py": os.path.join(ROOT, "plugin", "skills", "verify-loop", "scripts"),
    "features.py": os.path.join(ROOT, "plugin", "skills", "feature-map", "scripts"),
    "graph-audit.py": os.path.join(ROOT, "plugin", "skills", "latent-audit", "scripts"),
    "wire.py": os.path.join(ROOT, "plugin", "skills", "wire-check", "scripts"),
    "debug.py": os.path.join(ROOT, "plugin", "skills", "debug-protocol", "scripts"),
    "structure-report.py": os.path.join(ROOT, "plugin", "skills", "structure-gate", "scripts"),
    "structure.py": os.path.join(ROOT, "plugin", "skills", "structure-gate", "scripts"),
    "threat.py": os.path.join(ROOT, "plugin", "skills", "threat-model", "scripts"),
    "evolve.py": os.path.join(ROOT, "plugin", "skills", "evolve-maintain", "scripts"),
    "dep-map.py": os.path.join(ROOT, "plugin", "skills", "arch-design", "scripts"),
    "change-map.py": os.path.join(ROOT, "plugin", "skills", "arch-design", "scripts"),
    "arch-design.py": os.path.join(ROOT, "plugin", "skills", "arch-design", "scripts"),
    "perf.py": os.path.join(ROOT, "plugin", "skills", "perf-optimize", "scripts"),
    "release.py": os.path.join(ROOT, "plugin", "skills", "safe-release", "scripts"),
    "blast.py": os.path.join(ROOT, "plugin", "skills", "blast-radius", "scripts"),
    "mistake.py": os.path.join(ROOT, "plugin", "skills", "mistake-proof", "scripts"),
}


def run(tool, *args, stdin=None):
    """Invoke a tool through its CLI; return (returncode, stdout, stderr)."""
    p = subprocess.run(
        [sys.executable, os.path.join(SCRIPTS[tool], tool), *args],
        input=stdin, capture_output=True, text=True, encoding="utf-8",
    )
    return p.returncode, p.stdout, p.stderr
