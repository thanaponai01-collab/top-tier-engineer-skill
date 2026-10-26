"""Give the scratch copy git history: the accounts app as it runs today, then Dana's paid-plans PR
merged on top with a merge commit (the one RELEASE.md says to revert).

The copy already holds the merged files; this writes the state before the PR, commits it, commits
the PR on a branch, merges it, and leaves the files byte for byte as they were, so only .git is new.
"""
import os
import subprocess
import sys

ROOT = sys.argv[1]
CASE = os.path.dirname(os.path.abspath(__file__))
PR_ONLY = ["app/billing.py", "migrations/m0003_plans.py", "RELEASE.md"]
PR_CHANGED = ["app/users.py", "tests/test_accounts.py"]

TEST_BEFORE = '''import os
import subprocess
import sys
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class AccountsTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(ignore_cleanup_errors=True)
        os.environ["APP_DB"] = os.path.join(self.tmp.name, "test.db")
        subprocess.run([sys.executable, "migrate.py", "up"], cwd=ROOT, check=True, capture_output=True)

    def tearDown(self):
        del os.environ["APP_DB"]
        self.tmp.cleanup()

    def test_signup(self):
        from app import users
        uid = users.signup("Ana", "Ana@Example.com ")
        self.assertEqual(users.get_user(uid)["email"], "ana@example.com")

    def test_one_account_per_email(self):
        from app import users
        users.signup("Ana", "ana@example.com")
        with self.assertRaises(ValueError):
            users.signup("Ana again", "ANA@example.com")


if __name__ == "__main__":
    unittest.main()
'''


def path(name):
    return os.path.join(ROOT, *name.split("/"))


def read(name):
    with open(path(name), "rb") as fh:
        return fh.read()


def write(name, data):
    with open(path(name), "wb") as fh:
        fh.write(data if isinstance(data, bytes) else data.encode("utf-8"))


def git(*args, who="sam", when="2026-10-01T10:00:00+00:00"):
    env = dict(os.environ, GIT_AUTHOR_NAME=who, GIT_AUTHOR_EMAIL=f"{who}@example.invalid",
               GIT_COMMITTER_NAME=who, GIT_COMMITTER_EMAIL=f"{who}@example.invalid",
               GIT_AUTHOR_DATE=when, GIT_COMMITTER_DATE=when)
    subprocess.run(["git", "-c", "init.defaultBranch=main", "-c", "commit.gpgsign=false", "-c", "core.autocrlf=false",
                    *args], cwd=ROOT, env=env, check=True, capture_output=True)


final = {name: read(name) for name in PR_ONLY + PR_CHANGED}
with open(os.path.join(CASE, "reference", "original", "app", "users.py"), "rb") as fh:
    users_before = fh.read()

git("init", "-q")
for name in PR_ONLY:
    os.remove(path(name))
write("app/users.py", users_before)
write("tests/test_accounts.py", TEST_BEFORE)
git("add", "-A")
git("commit", "-q", "-m", "accounts: sign-up, last login")

git("checkout", "-q", "-b", "dana/paid-plans")
for name, data in final.items():
    write(name, data)
git("add", "-A")
git("commit", "-q", "-m", "Paid plans: users.plan, billing.set_plan", who="dana", when="2026-10-24T16:20:00+00:00")
git("checkout", "-q", "main")
git("merge", "-q", "--no-ff", "dana/paid-plans", "-m", "Merge pull request #57 from dana/paid-plans",
    who="sam", when="2026-10-26T09:05:00+00:00")
for name, data in final.items():
    assert read(name) == data, name
