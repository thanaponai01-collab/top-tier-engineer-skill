I rewrote `fixture/doctor.py`. It now fails a healthy but stale process, and it passes when the running process matches the working tree. I did not run the full strict loop (no `baseline` or `run --strict`), so there is no `VERIFY-STATE: green` yet.

**What it does now.** The doctor reads `/identity` from the running process. It compares that with values computed from the files on disk at that moment:
- the SHA-256 of `app.py`, so uncommitted edits count
- the SHA-256 of `config.json`
- flags, role and mocks
- a positive PID

On a mismatch it exits nonzero with a line like `running artifact identity mismatch: source_sha256: expected …, observed …` for each field. The app and `config.json` are unchanged.

**Checked on a scratch copy** with the port set to 18765, then the same rejection once through `verify.py run`:
- **Unchanged tree:** passes.
- **Dirty source:** an uncommitted line added to `app.py` is rejected with the `source_sha256` mismatch. `verify.py run` reported `Run: doctor failed; no check was run.` with that output.
- **Changed config:** edits to flags, role and mocks are each rejected, with expected and observed values shown.
- **Fixture restored:** I put `config.json` and `app.py` back afterward and checked that `config.json` is the original.

**One thing you need to know.** `config.json` has `"port": 0`, so the server binds a random port and the doctor can't find it. I didn't change that. The doctor reads `SERVICE_PORT` from the environment when the config port is 0. If neither is set, it fails with the same mismatch message.

**Other changes and gaps:**
- I edited `VERIFY.md`: the `Service identity` oracle is now `config.json` only, and the blind-spots note describes the new doctor. I didn't verify that `verify.py` records that blind-spots line.
- `VERIFY.md` has no `start`/`ready` lines, so `verify.py` doesn't launch the service. It needs a live instance with `SERVICE_PORT` set.
- The `Service identity` section's own test is still the placeholder `print`. The identity check lives only in the Run doctor.