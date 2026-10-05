# VERIFY.md Reference & Schema

`VERIFY.md` lives at the repo root. It maps each feature in the codebase to runnable commands that prove it works.

## Format Overview

```markdown
## Feature Name
- test: `python -m pytest tests/test_feature.py -q`
- run: `python scripts/smoke_driver.py`
- oracle: SPEC.md, data/feature_cases.json, scripts/smoke_driver.py
- schema: `python scripts/compliance.py schema schemas/feat.json out/feat.json --strict`
- privacy: `python scripts/compliance.py privacy out/`
- fail-proof: changed the return status, test went red, reverted

## Journey: Complete Flow
- features: Feature A, Feature B
- test: `python -m pytest tests/test_flow.py -q`
- fail-proof: broke the handoff between A and B, flow test failed, reverted

## Run
- setup: `python scripts/seed.py`
- start: `python app.py`
- ready: `python scripts/wait_http.py http://localhost:8000/health`
- doctor: `python scripts/check_instance.py`
- stop: `python scripts/shutdown.py`
- login: user demo@example.com, password in .env.test

## Blind spots
- third-party payment gateway is mocked; live card decline path is not exercised
```

---

## Sections Explained

### 1. `## <Feature>`
- Each bullet is `kind: <command>`, `fail-proof: <text>` or `oracle: <files>`.
- A check passes when its command exits 0.
- `fail-proof:` explains the controlled wrong state and intended failure signal. Strict runs also
  require a retained failing command/output for the current check hashes; a sentence alone fails.
- `oracle:` lists comma-separated repo-relative spec, fixture and helper files to freeze, alongside
  automatically frozen tests and commands. Missing files fail. Keep implementation files out.
- Failure receipts bind all mapped commands, tests, oracles and the Run recipe. After changing
  these definitions, demonstrate rejection again. A timeout is not a receipt.

### 2. `## Journey: <name>`
- Cross-cutting flows linking multiple features.
- `features:` must list two or more features that each have their own section.
- Checks run the end-to-end seam.

### 3. `## Run`
- How to bring up the application when `run:` checks require a live server or service.
- `setup`: Executed before start (e.g. database seed).
- `start`: Launched in the background.
- `ready`: Polled until it exits 0 before checks execute.
- `doctor`: Optional read-only identity/build/auth check after readiness and before checks; also
  supports an externally managed instance without `start`.
- `stop`: Optional shutdown command (otherwise the process group is terminated).
- `login`: Login/role instructions; refer to secrets by location rather than recording their values.

### 4. `## Blind spots`
- Things that cannot be tested locally or are deliberately stubbed.
- A green run prints these so readers know what is untested.

## Completion

`run --strict` rejects failed checks, unverified features, missing rejection evidence and orphan
test files. Name each test file or its folder in a command so the map can attribute it. Strict
green covers mapped claims only; it does not prove the feature inventory is complete.

`status` requires the last whole run to be strict, green and unchanged by content. A non-strict
pass is `partial`; a failed strict run stays red. Output tails and rejection receipts remain in
.verify-state.json after app teardown. Capture larger artifacts separately and redact secrets.
Commands run through the shell like a Makefile: run recipes only from a repo you trust.
