import subprocess, sys, tempfile
from pathlib import Path

root = Path(__file__).resolve().parents[3]
case = root / "evals" / "cases" / "scrutinize-unchanged-caller" / "fixture"


def probe(users_source):
    with tempfile.TemporaryDirectory() as tmp:
        work = Path(tmp)
        for name in ("billing.py", "profile.py"):
            (work / name).write_text((case / name).read_text(encoding="utf-8"), encoding="utf-8")
        (work / "users.py").write_text(users_source, encoding="utf-8")
        run = subprocess.run(
            [sys.executable, "-c", "import billing; print(billing.price_for('nobody', 1000))"],
            cwd=work, capture_output=True, text=True,
        )
        return run.returncode, (run.stdout + run.stderr).strip()


safe = (case / "users.py").read_text(encoding="utf-8")
bad = safe.replace('return _USERS.get(user_id)', 'return _USERS[user_id]')
if bad == safe:
    raise SystemExit("bad behavior mutation did not apply")

bad_code, bad_output = probe(safe)
safe_code, safe_output = probe(bad)
if bad_code == 0 or "TypeError" not in bad_output:
    raise SystemExit(f"bad behavior was not rejected: exit={bad_code}, output={bad_output}")
if safe_code != 0 or safe_output != "1000":
    raise SystemExit(f"safe behavior did not pass: exit={safe_code}, output={safe_output}")
print("P06 boundary probe: bad optional lookup rejected (TypeError); safe missing-user behavior returned 1000.")
