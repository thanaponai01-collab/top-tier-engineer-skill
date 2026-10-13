`doctor.py` now rejects a healthy old process when its source or runtime settings differ from the files on disk.

I tested it on a scratch copy with a nonzero port, since the shipped `config.json` has `"port": 0`. A fresh server passed. After I changed `role` in the config, the doctor exited 1 and named `config_sha256` and `role`. After I also edited `app.py`, it named `source_sha256` too.

- **What it checks:** the doctor calls the app's own `identity()` on the current files. It compares `source_sha256`, `config_sha256`, `flags`, `role` and `mocks` against what the running process reported at startup. It ignores `pid`, which is expected to differ. Because it hashes file contents rather than a revision id, uncommitted edits with an unchanged revision are caught.
- **The reason it records:** on a mismatch it exits non-zero with `identity mismatch: pid N is healthy but stale (<field>: running=… current=…); restart the service from the current source/config`.
- **`VERIFY.md`:** it now spells out the pass, fail and on-mismatch behavior, and the requirement that the record keep the mismatch reason. I added that it can't detect changes to things `identity()` doesn't hash, such as imported modules or environment variables.
- **App contract:** `app.py` and `config.json` are untouched.

The doctor reads `/identity` on `settings['port']`, and the shipped config has port 0, so it can't connect to a real server until a fixed port is set. I left that alone because it isn't part of this fix.