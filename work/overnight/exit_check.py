"""Exit check for the 2026-10-11 overnight run: every skill has an eval case, the suite is green,
and every newly covered case has been run live in both arms. A skill failing its case is a finding,
not a failure of this check; a case never run live is."""
import glob, json, os, subprocess, sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
NEWLY = ["agent-design", "agent-drift", "agent-evals", "agent-prove", "agent-release", "agent-trace",
         "arch-map", "code-history", "evolve-maintain", "explain", "feature-map", "issue-handoff",
         "onboard-system", "pick-skill", "problem-framing", "recall", "scrutinize"]
RESULTS = os.path.join(ROOT, "evals", "results", "coverage-2026-10-11")
bad = []
listed = [l.strip() for l in open(os.path.join(ROOT, "evals", "uncovered.txt"), encoding="utf-8")
          if l.strip() and not l.startswith("#")]
if listed:
    bad.append(f"uncovered.txt still lists: {', '.join(listed)}")
cases = {}
for p in glob.glob(os.path.join(ROOT, "evals", "cases", "*", "expect.json")):
    c = json.load(open(p, encoding="utf-8"))
    cases.setdefault(c["skill"], []).append(c["case"])
for skill in NEWLY:
    names = cases.get(skill)
    if not names:
        bad.append(f"{skill}: no case")
        continue
    for name in names:
        for arm in ("with", "without"):
            runs = glob.glob(os.path.join(RESULTS, name, f"{arm}-*", "result.json"))
            ok = [r for r in runs if not json.load(open(r, encoding="utf-8")).get("errored")]
            if not ok:
                bad.append(f"{name}: no completed live {arm} run")
proc = subprocess.run([sys.executable, "-m", "unittest", "discover", "tests"], cwd=ROOT,
                      capture_output=True, text=True)
if proc.returncode:
    bad.append("unit tests red: " + proc.stderr.strip().splitlines()[-1])
print("\n".join(bad) or "EXIT CHECK: every skill covered, suite green, every new case run live")
sys.exit(1 if bad else 0)
