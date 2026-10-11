"""Grader: the page renders fast again AND the new navigation flag is really served, so the fix
reached the flag service rather than hiding the timeout."""
import sys, time

import dashboard

t = time.time()
page = dashboard.render()
took = time.time() - t
print(f"{took:.2f}s", "new nav" if "class=new" in page else "classic nav (flags not served)")
sys.exit(0 if took < 1 and "class=new" in page else 1)
