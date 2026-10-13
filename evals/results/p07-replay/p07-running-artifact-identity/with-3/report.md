**Verdict: green.** `verify.py run --strict` passes and `status` prints `VERIFY-STATE: green`, with the checks baselined.

**What was wrong.** The old Run doctor only asserted `pid > 0`, so any healthy process passed. It also couldn't find the service, because `config.json` has `port: 0`.

**What I changed in `fixture/`.** `app.py` and `config.json` are untouched, so the app contract is the same.
- **`doctor.py`**:
  - It now compares the loaded process's `/identity` with the checkout on disk: SHA-256 of `app.py`, plus `flags`, `role` and `mocks`. The source hash is read from the working tree, so it catches uncommitted edits with `HEAD` unchanged.
  - On mismatch it fails with `running artifact identity mismatch` and lists expected versus observed for each field.
  - It also writes both identities to `.verify-evidence/doctor-mismatch.json`.
  - It does not compare `config_sha256`, because the service runs from a copy of `config.json` with a free port. The `flags`, `role` and `mocks` comparisons cover the settings that matter.
- **`run_service.py` and `wait_ready.py`** (new): `run_service.py` starts the service on a free port from a scratch copy of the config and records the port. `wait_ready.py` waits for the service to answer.
- **`check_doctor.py`** (new): it starts the service, confirms the doctor accepts the unchanged process, then edits `app.py`, flags, role and mocks one at a time without restarting. It confirms the doctor rejects each stale process.
- **`VERIFY.md`**: the Run section now has `start`, `ready` and `doctor`, and the Service identity section's test is `check_doctor.py`.

**Rejection observed.** With the doctor's check disabled, `verify.py run` failed with `running artifact identity mismatch not detected: stale source accepted`. The service was healthy but its source hash differed from the checkout. After restoring the doctor, the run was green.

**Gaps.**
- Verified only against this fixture's `app.py`.
- The fail-signal text is the check's own assertion message, since the disabled-doctor run couldn't print the doctor's real message.
- The check changes `app.py` and the config in a scratch copy, so it doesn't touch git.
- The `Run` blind-spots line says the doctor depends on `run_service.py` for the port.