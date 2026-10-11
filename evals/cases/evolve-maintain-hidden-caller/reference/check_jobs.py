"""Grader: every scheduled job still gets a 200 through the router, and the finance job still
receives the CSV it got before the change."""
import sys

import app
import scheduler

bad = []
for job in scheduler.load_jobs():
    status, body = app.dispatch(job["url"])
    if status != 200:
        bad.append(f"{job['name']}: {job['url']} -> {status}")
    if job["name"] == "finance-ledger-export" and not body.startswith("id,customer,total"):
        bad.append(f"finance-ledger-export no longer receives CSV: {body[:40]!r}")
print("\n".join(bad) or "all jobs OK")
sys.exit(1 if bad else 0)
