I updated the project memory for the login return-URL change. The second upkeep pass changed no context documents. No change range or diff was supplied, so I worked from `CHANGE.md`'s before/after description and the current source.

**Updated**
- `work/auth.md`: login now keeps its return URL. Session expiry is still listed as unfinished, and the requirement stays linked to `BRIEF.md`.
- `work/redirect.md`: `preserve(target)` now returns `target` instead of `/`.
- `BUILD.md`: the login fix is marked done, and `work/redirect.md` is now listed. `work/billing.md` is untouched, so the invoice-rounding decision is still open.

**Index and check passes**
- First pass: the index step updated 3 files and the check found no issues.
- Second pass: after `python tools/upkeep_probe.py capture`, the index step changed 0 files and the check found no issues. `compare` also reported the documents unchanged.
- These checks are structural only; they don't test product behavior.

**Gaps**
- No tests ran, so every record still says `tests/test_navigation.py` was not run.
- This change also affects checkout. It calls `preserve('/billing')`, which used to return `/` and now returns `/billing`. No billing record covers checkout, so I noted it in `work/redirect.md` as a coverage gap. The owner should confirm that behavior is intended.

**Next:** implement session expiry in `src/auth`. It's done when expired sessions are rejected and `tests/test_navigation.py` plus a new expiry test pass.