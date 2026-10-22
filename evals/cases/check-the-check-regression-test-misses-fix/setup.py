"""Give the scratch copy the PR's history: main before the fix, then the PR commit.

Before the fix, invoice_total() worked out the fee itself with `>=`, so paying on the due date was
charged; late_fee() was already right. The PR routes invoice_total() through late_fee() and adds a
regression test that calls late_fee() only. The final files are restored byte for byte, so only
.git is new.
"""
import os
import subprocess
import sys

ROOT = sys.argv[1]

BILLING_BEFORE = '''from datetime import date

LATE_FEE_RATE = 0.05


def late_fee(due: date, paid: date, amount: float) -> float:
    """Fee for paying `amount` on `paid` when it was due on `due`. Paying on the due date is on time."""
    if paid > due:
        return round(amount * LATE_FEE_RATE, 2)
    return 0.0


def invoice_total(amount: float, due: date, paid: date) -> float:
    """What the customer owes: the amount plus any late fee."""
    fee = round(amount * LATE_FEE_RATE, 2) if paid >= due else 0.0
    return round(amount + fee, 2)
'''


def read(rel):
    with open(os.path.join(ROOT, rel), encoding="utf-8", newline="") as fh:
        return fh.read()


def write(rel, text):
    with open(os.path.join(ROOT, rel), "w", encoding="utf-8", newline="") as fh:
        fh.write(text)


def git(*args, author="Dana Reyes <dana@example.com>"):
    name, mail = author[:-1].split(" <")
    env = dict(os.environ, GIT_AUTHOR_NAME=name, GIT_AUTHOR_EMAIL=mail,
               GIT_COMMITTER_NAME=name, GIT_COMMITTER_EMAIL=mail,
               GIT_AUTHOR_DATE="2026-04-01T10:00:00", GIT_COMMITTER_DATE="2026-04-01T10:00:00")
    subprocess.run(["git", *args], cwd=ROOT, check=True, capture_output=True, env=env)


final = {rel: read(rel) for rel in ("billing.py", "test_billing.py", "PR.md")}
test_before = final["test_billing.py"].replace(
    '''
    def test_due_date_is_not_late(self):
        # Regression test for #12: a customer who pays on the due date was charged a late fee.
        self.assertEqual(late_fee(DUE, DUE, 200.0), 0.0)
''', "")
assert test_before != final["test_billing.py"]

git("init", "-q", "-b", "main")
os.remove(os.path.join(ROOT, "PR.md"))
write("billing.py", BILLING_BEFORE)
write("test_billing.py", test_before)
git("add", "-A")
git("commit", "-q", "-m", "Billing: late fees and invoice totals")
git("switch", "-q", "-c", "fix-12-due-date-fee")
for rel, text in final.items():
    write(rel, text)
git("add", "-A")
git("commit", "-q", "-m", "Don't charge a late fee on the due date (fixes #12)", author="Sam Okafor <sam@example.com>")
