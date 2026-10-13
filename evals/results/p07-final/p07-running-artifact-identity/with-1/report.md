`verify.py status` now prints `VERIFY-STATE: green` after `run --strict`. The Run doctor rejects a healthy process that was started from older source or with different flags, role or mocks.

**What was wrong:** `doctor.py` only checked that `/identity` answered with a positive PID. A healthy process built from old code passed.

**What changed (all in `fixture/`; `app.py` and `config.json` are untouched):**
- **`doctor.py`:** It recomputes the expected identity from the files on disk and compares it with what the live process reports. That covers `source_sha256` of `app.py` (so uncommitted edits count), `flags`, `role`, `mocks` and a positive `pid`. A mismatch prints `running artifact identity mismatch`, then expected versus observed for each field and the full observed identity, and exits 1. It reads the port from `SERVICE_PORT`, then `.verify-port`, then `config.json`, and rejects port 0.
- **`serve_verify.py` (new):** `config.json` has `port: 0`, which the doctor can't address. This helper starts an unmodified copy of `app.py` on a free port and records that port for the doctor. Only the copy's port changes, so the app contract is the same.
- **`test_doctor.py` (new):** Starts a process, then changes the tree afterwards, so the process is older than the files. It passes when nothing changed and rejects an uncommitted source edit, changed flags, changed role and changed mocks.
- **`VERIFY.md`:** The "Service identity" feature now runs `test_doctor.py`. The Run section gained `start`, `ready` and the doctor, and there is a blind spot note.

**Rejection observed:** I put a weak health-only doctor back, and the check failed on all four stale cases with `expected exit != 0 with 'running artifact identity mismatch', got exit=0`. I then restored the real doctor, re-baselined, ran `run --strict`, and `status` was green. Strict reports 0 unproven features, so the failing receipt counts.

**Gaps:**
- **Port override:** The identity check compares `source_sha256`, `flags`, `role` and `mocks`, but not `config_sha256` (a port-injected copy would always differ). A config change that doesn't touch those three fields would not be caught.
- **Scope:** The identity does not cover anything `app.py` imports beyond the standard library.
- **Test method:** The stale-process cases run in scratch copies of the tree, not against the Run-managed instance.
- **Weak-doctor check:** The weak doctor I swapped in was a hand-written stand-in for the original, not the original file.
- **Re-baselining:** I re-baselined several times as I edited the check files myself. A person should review `test_doctor.py` and `VERIFY.md` before trusting that baseline.