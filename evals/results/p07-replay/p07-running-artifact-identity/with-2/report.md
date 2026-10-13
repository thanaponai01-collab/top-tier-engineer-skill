I fixed the Run doctor in `fixture/doctor.py`. I did not run `verify.py` (`run --strict`, `baseline`, `status`), so the VERIFY.md checks have no recorded receipts. I tested the doctor by hand on a scratch copy of the fixture. I changed `app.py` and `config.json` only in that copy, never in `fixture/`.

**What the doctor does now.** It reads `app.py` and `config.json` as they are on disk, hashes both, and compares them to what the live `/identity` endpoint reports. The comparison covers the source hash, config hash, flags, role and mocks, and it still requires a positive pid. On any mismatch it exits 1. It writes an expected-versus-actual diff to stderr, and the full live and expected identities to stdout. Because it hashes the working-tree files, an uncommitted edit is caught even when `HEAD` hasn't moved.

**What I saw.** On the scratch copy with the server started on port 18765:
- With unchanged files, the doctor passed.
- After appending a comment to `app.py` while the server kept running, it exited 1 and showed the old and new source hashes.
- After restoring `app.py`, it passed again.
- After changing the role in `config.json` from `api` to `worker`, it exited 1. It flagged both `role` and `config_sha256`.

I didn't test flag or mock changes separately. They use the same comparison as role.

**Port.** `config.json` has `port: 0`, so the old doctor couldn't have reached the service on that port. The doctor now uses a `DOCTOR_PORT` environment variable when set, and otherwise the config port. Whoever launches the service needs to set `DOCTOR_PORT` to the port it actually bound. `app.py` and `config.json` are unchanged, so the app contract is the same.

**Still open.** I left `VERIFY.md` as it was, so the doctor's rejection isn't proven in the skill's recorded workflow yet. Its Service identity test is just an `echo`, and the strict green step is not done. The doctor only checks that the running process matches the files on disk. A process started from the same files with different command-line arguments would still pass.