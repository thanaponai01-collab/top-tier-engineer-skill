I rewrote `doctor.py` and `VERIFY.md` so a healthy old process fails the check when `app.py` or `config.json` has changed since it started. I haven't run any of it. `app.py` is unchanged, so its `/identity` contract is the same.

**What the doctor does now**
- It hashes the current `app.py` and `config.json` and reads `flags`, `role` and `mocks` from the config.
- It compares those against what the process on the port reports for `source_sha256`, `config_sha256`, `flags`, `role` and `mocks`.
- It never uses the revision id, so uncommitted edits are caught.
- `pid` is excluded from the comparison because it always differs between processes.
- On a mismatch it exits 1 and prints one line, for example `FAIL: stale process pid=… on port … differs from files on disk (source_sha256: running=… expected=…); restart the service`.
- On a match it prints the identity and exits 0, as before.

**What `VERIFY.md` now says**
- It states the pass condition, tells you to record the `FAIL:` line as the reason, and says to restart and rerun.
- It lists the blind spots: `pid` isn't compared, and environment variables and files other than `app.py` and `config.json` aren't covered.

The fixture's `config.json` has `"port": 0`, which makes the doctor probe `127.0.0.1:0`. I left that alone, so you'll need a real port before the doctor can reach a service.