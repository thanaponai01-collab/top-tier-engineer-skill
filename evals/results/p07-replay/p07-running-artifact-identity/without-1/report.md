The doctor now rejects a healthy old process when `app.py` or `config.json` on disk no longer matches what that process loaded. I ran it against a copy of the fixture and it behaved as intended. I didn't change `app.py`, so the `/identity` contract is untouched.

**What changed**
- **`fixture/doctor.py`:**
  - It hashes `app.py` and `config.json` as they are on disk, so uncommitted edits count and Git HEAD plays no part.
  - It compares those hashes, plus `flags`, `role` and `mocks`, with what `/identity` reports.
  - It prints one JSON verification record and exits 0 only on a pass.
  - On a mismatch the record has `status: "fail"` and a `reason` that names each differing field with its running and disk values. The record also includes the `running` and `expected` identities.
  - Unreachable or unresponsive services produce a failing record with a reason, not a traceback.
  - It now reads both files from its own directory, not the current working directory.
- **`fixture/VERIFY.md`:** The test, oracle, fail-signal and fail-proof entries describe the new check and the record format. It also says to restart `python app.py serve` after editing, and lists the blind spots: env vars and other modules aren't compared.

**Test:** I used a copy with the port set to 18765 and started the server.
- **Unchanged files:** `status: pass`, exit 0.
- **After editing `role` in `config.json`:** the same process still answered healthy, but the doctor failed with exit 1. The reason named `config_sha256` and `role`.

**Port 0:** The shipped `config.json` has `"port": 0`. The doctor can't probe that port, so it reports a failing record with a probe-failed reason. I left the config alone because the port looked like a deliberate placeholder. Set the real port before using the doctor.