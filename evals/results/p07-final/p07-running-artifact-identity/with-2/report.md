The doctor is fixed and passes my stale-process test. I couldn't get a green `verify.py` run, because the fixture has no reachable service for the doctor to check.

**What I changed**
- **`doctor.py`**: It now recomputes the expected identity from the files on disk, including uncommitted edits. It compares that with what the live process reports for source digest, config digest, flags, role and mocks. Any mismatch prints `running artifact identity mismatch` with expected versus observed per field and exits 1. The PID check is kept. The port comes from `SERVICE_PORT` if set, otherwise from `config.json`.
- **`identity_check.py`** (new): It copies the fixture to a scratch directory and starts the real service on a free port. The current process is accepted. Then, without restarting the process or committing anything, it edits the source, flags, role and mocks in turn. The still-healthy old process is rejected each time with the matching expected-versus-observed line.
- **`VERIFY.md`**: The "Service identity" test now runs `identity_check.py`, which was previously a placeholder `print`. I updated the doctor blind spots too.
- **Contract**: `app.py` and `config.json` are unchanged.

**Evidence**
- `python identity_check.py` printed `rejected stale source_sha256`, `flags`, `role`, `mocks`, then `running artifact identity verified`.

**Not done**
- `verify.py run` stops at the doctor. `config.json` has `"port": 0` and `VERIFY.md` has no `start`/`ready` step, so no service is running for it to check. Port 0 only means "pick a random port", so there is nothing fixed to point `ready` at.
- `verify.py status` reports `red` (two runs in a row), and I did not get the strict run to green. I did run `baseline`, so the check files are frozen at the current versions.
- The fix is to set a real port in `config.json`, or to export `SERVICE_PORT` and add `start: python app.py serve` and a `ready` line. I left that to you, since `config.json` is part of the contract and a real port may be your call.
- The doctor tests the stale-process cases through `identity_check.py`. A deliberately stale live process on the expected port has not been exercised through `verify.py` itself.