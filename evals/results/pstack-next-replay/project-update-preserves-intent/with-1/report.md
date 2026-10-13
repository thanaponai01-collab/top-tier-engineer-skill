I updated three context documents to record the change. The second index/check pass changed no context documents. `upkeep_probe.py compare` printed "upkeep documents unchanged".

The project root is `fixture/`. No change range was given, so I used the before/after in `CHANGE.md` and read the current callers.

- **Updated:** `BUILD.md`, `work/auth.md` and `work/redirect.md`. They now say that `preserve(target)` returns `target`, where it used to return `/`, and that login keeps its return URL. They also record that checkout now returns `/billing` instead of `/`.
- **Kept as it was:**
  - Session expiry is still marked unfinished, and `BRIEF.md` is untouched.
  - `work/billing.md`, including its unresolved invoice-rounding item, is untouched.
  - `docs/architecture.md` is untouched because no boundary, wiring or placement changed.
  - I added `work/redirect.md` to the `BUILD.md` includes so the shared helper's record is reachable from the work file.
- **Checks:** The helper's structural check reported no issues on both passes. That covers links and size only, not whether the code works.
- **Evidence gap:** No tests ran, so the change is recorded as unverified. `tests/test_navigation.py` already asserts the new login and checkout results, but I did not run it.

**Next:** run `tests/test_navigation.py`; it is done when both tests pass. After that, start session expiry.