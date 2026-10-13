The Run doctor is fixed, but I couldn't get `verify.py` to go fully green. `VERIFY-STATE` is red because it hit its 5-red budget, and the strict run reports the feature as unproven.

**The fix**
- `fixture/doctor.py` now computes the expected identity from the working tree by calling `app.identity()`. It compares that with what the live process captured at startup: source sha256 of `app.py` (uncommitted bytes included), config sha256, flags, role and mocks. `HEAD` plays no part.
- On any mismatch it prints `running artifact identity mismatch:` and, for each field, the expected and observed values. It exits 1 and prints both full identities, so the evidence stays in the run receipt.
- `config.json` has `port: 0` (ephemeral), which the doctor cannot dial. The doctor reads the bound port from `SERVICE_PORT` and falls back to the config port. I did not change the app or config contract.
- `VERIFY.md`: the Run doctor note and blind spot are updated. The feature test is now `python doctor.py` instead of a placeholder that could never fail. I removed the `oracle:` line, because it listed the implementation files `app.py` and `config.json`, which the format says to keep out.

**What I observed**
- In a scratch copy, an unchanged tree passed.
- A healthy old process was rejected for:
  - an uncommitted one-line edit to `app.py`, with no commit involved;
  - changed flags;
  - a changed role;
  - a changed mock.
- Each rejection named the expected-versus-observed values.
- Through `verify.py run`, the doctor gate failed with the source-hash mismatch against a live process started from the older `app.py`. It passed once the tree matched.

**What is not done**
- `verify.py` records no failing receipt for the doctor gate. The doctor runs before the feature checks and stops the run, so strict still reports "no recorded failing run matching fail-signal". I did not find a way to produce that receipt without removing the doctor from the recipe, which would defeat the fix.
- The identity only proves what the process captured at startup. A process that lies about its identity would not be caught. This is listed as a blind spot.

**My mistakes**
- My driver script briefly truncated `app.py`. I restored it, and its sha256 matches the original (`40691174…`).
- `VERIFY.md` is restored to the final content described above.
- `.verify-state.json` and the scratch scripts (`drive.py`, `drive2.py`, `V.bak`) are left in the fixture's parent directory.

Decision for you: if you want strict green, how should the doctor gate be handled? One option is to let the feature test run without the doctor gate against a stale instance, so it produces the receipt. The other is to extend `verify.py` to accept a doctor failure as one.