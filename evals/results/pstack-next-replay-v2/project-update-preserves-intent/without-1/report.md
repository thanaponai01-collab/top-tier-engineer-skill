The project memory now matches the completed login change, and the second index/check pass changed no context documents. No tests have run. `check` only validates structure, not product correctness.

**What I updated**
- `BUILD.md`: the return URL fix is marked implemented with checks not run, and session expiry stays unfinished. I added `work/redirect.md` to the includes, since nothing linked it. The next step now reads: run the navigation tests, then implement session expiry.
- `work/auth.md`: login now keeps its return URL through `preserve(target)`. Session expiry stays open and the check is still marked not run.
- `work/redirect.md`: `preserve(target)` now returns `target` instead of always `/`. I also noted that checkout calls it with `/billing` and now gets `/billing` back, so someone should confirm that was intended.

I left `BRIEF.md`, `AGENTS.md`, `docs/architecture.md` and `work/billing.md` untouched, so the owner requirement and the open invoice rounding item are preserved.

**Index/check passes**
- **First pass:** the first `index` run reported 3 files changed, and `check` found no issues. My first edit script stopped partway, so I fixed the remaining two files and re-ran. That second `index` reported 2 files changed, and `check` was clean again.
- **Probe capture:** `upkeep_probe.py capture` recorded 5 context documents.
- **Repeat pass:** `index` reported 0 files changed, `check` was clean, and `upkeep_probe.py compare` said "upkeep documents unchanged".

**Next step:** run `tests/test_navigation.py`, then implement session expiry. Also decide whether the changed checkout behavior is intended.