"""Give the scratch copy a year of history: what changes and gets fixed, and what never moves.

The copy already holds the final files. This writes the earlier states, commits each, and ends
with every file byte for byte as it was, so only .git is new.

- The discount rule lives in shop/cart.py and again in shop/receipt.py, with no import between
  them. They change together in 5 commits, 2 of them fixes, and one fix touched only receipt.py.
- Two HTTP clients (urllib in notify.py, http.client in payments.py) each got their own retry
  and timeout fixes.
- legacy/tax_tables.py, the ugliest function in the repo, is touched only by the first commit.
"""
import os
import subprocess
import sys

ROOT = sys.argv[1]


def read(name):
    with open(os.path.join(ROOT, *name.split("/")), "rb") as fh:
        return fh.read().decode("utf-8")


def write(name, text):
    with open(os.path.join(ROOT, *name.split("/")), "wb") as fh:
        fh.write(text.encode("utf-8"))


def git(*args, when=None):
    env = dict(os.environ, GIT_AUTHOR_NAME="dev", GIT_AUTHOR_EMAIL="dev@example.invalid",
               GIT_COMMITTER_NAME="dev", GIT_COMMITTER_EMAIL="dev@example.invalid")
    if when:
        env.update(GIT_AUTHOR_DATE=when, GIT_COMMITTER_DATE=when)
    subprocess.run(["git", "-c", "init.defaultBranch=main", "-c", "commit.gpgsign=false", *args],
                   cwd=ROOT, env=env, check=True, capture_output=True)


def commit(msg, when):
    git("add", "-A")
    git("commit", "-q", "-m", msg, when=when)


FINAL = {}
for d, _, names in os.walk(ROOT):
    if ".git" in d.split(os.sep):
        continue
    for n in names:
        rel = os.path.relpath(os.path.join(d, n), ROOT).replace(os.sep, "/")
        FINAL[rel] = read(rel)

ROUND = "(subtotal * (100 - pct) + 50) // 100"


def rule(name, member, threshold, rounded=True):
    text = FINAL[name].replace("MEMBER_DISCOUNT_PCT = 10", f"MEMBER_DISCOUNT_PCT = {member}")
    text = text.replace("BULK_THRESHOLD = 5", f"BULK_THRESHOLD = {threshold}")
    return text if rounded else text.replace(ROUND, "subtotal * (100 - pct) // 100")


def notify(attempts, timeout, backoff):
    text = FINAL["shop/notify.py"].replace("range(3)", f"range({attempts})")
    text = text.replace("timeout=10", f"timeout={timeout}")
    return text if backoff else text.replace("time.sleep(2 ** attempt)", "time.sleep(0)")


PAY = FINAL["shop/payments.py"]
PAY_NO_CLOSE = PAY.replace("\n        finally:\n            conn.close()", "")
TESTS = ("tests/__init__.py", "tests/test_totals.py")

git("init", "-q")
for t in TESTS:
    os.remove(os.path.join(ROOT, *t.split("/")))
write("shop/cart.py", rule("shop/cart.py", 5, 10, rounded=False))
write("shop/receipt.py", rule("shop/receipt.py", 5, 10, rounded=False))
write("shop/notify.py", notify(1, 3, False))
write("shop/payments.py", PAY_NO_CLOSE.replace("range(4)", "range(1)"))
commit("shop: cart, receipts, checkout, payments, order emails, tax tables", "2025-11-03T10:00:00+00:00")

write("shop/cart.py", rule("shop/cart.py", 8, 10, rounded=False))
commit("member discount 5% -> 8%", "2025-12-01T10:00:00+00:00")
write("shop/receipt.py", rule("shop/receipt.py", 8, 10, rounded=False))
commit("fix: receipt total differs from cart for members", "2025-12-04T10:00:00+00:00")

write("shop/cart.py", rule("shop/cart.py", 8, 6, rounded=False))
write("shop/receipt.py", rule("shop/receipt.py", 8, 6, rounded=False))
commit("bulk discount from 10 items to 6", "2026-01-12T10:00:00+00:00")
write("shop/cart.py", rule("shop/cart.py", 8, 6))
write("shop/receipt.py", rule("shop/receipt.py", 8, 6))
commit("fix: receipt and cart round the discount differently", "2026-01-15T10:00:00+00:00")

write("shop/notify.py", notify(3, 3, False))
commit("notify: retry failed order emails", "2026-02-02T10:00:00+00:00")
write("shop/notify.py", notify(3, 10, False))
commit("fix: order emails time out under load", "2026-02-09T10:00:00+00:00")

write("shop/payments.py", PAY_NO_CLOSE)
commit("payments: retry on 502 and 503", "2026-03-03T10:00:00+00:00")
write("shop/payments.py", PAY)
commit("fix: payment retries leak connections", "2026-03-06T10:00:00+00:00")

write("shop/cart.py", rule("shop/cart.py", 10, 5, rounded=True).replace("BULK_EXTRA_PCT = 5", "BULK_EXTRA_PCT = 3"))
write("shop/receipt.py", rule("shop/receipt.py", 10, 5, rounded=True).replace("BULK_EXTRA_PCT = 5", "BULK_EXTRA_PCT = 3"))
commit("member discount 10%, bulk from 5 items", "2026-04-07T10:00:00+00:00")
write("shop/cart.py", FINAL["shop/cart.py"])
write("shop/receipt.py", FINAL["shop/receipt.py"])
commit("fix: bulk extra should be 5%, receipt and cart both showed 3%", "2026-04-09T10:00:00+00:00")

for t in TESTS:
    write(t, FINAL[t])
commit("test: the receipt total must match the cart", "2026-04-10T10:00:00+00:00")

write("shop/notify.py", FINAL["shop/notify.py"])
commit("fix: email retries hammer the webhook, back off", "2026-05-05T10:00:00+00:00")

for name, text in FINAL.items():
    write(name, text)
git("add", "-A")
status = subprocess.run(["git", "status", "--porcelain"], cwd=ROOT, capture_output=True, text=True).stdout
assert not status.strip(), status
