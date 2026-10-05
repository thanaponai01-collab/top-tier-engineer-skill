# VERIFY.md Reference & Schema

`VERIFY.md` lives at the repo root. It maps each feature in the codebase to runnable commands that prove it works.

## Format Overview

```markdown
## Feature Name
- test: `python -m pytest tests/test_feature.py -q`
- run: `python scripts/smoke_driver.py`
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
- stop: `python scripts/shutdown.py`
- login: user demo@example.com, password in .env.test

## Blind spots
- third-party payment gateway is mocked; live card decline path is not exercised
```

---

## Sections Explained

### 1. `## <Feature>`
- Each bullet is `kind: <command>` or `fail-proof: <text>`.
- A check passes when its command exits 0.
- `fail-proof:` is required for `--strict` runs. It notes what was broken intentionally to prove the check is not hollow.

### 2. `## Journey: <name>`
- Cross-cutting flows linking multiple features.
- `features:` must list two or more features that each have their own section.
- Checks run the end-to-end seam.

### 3. `## Run`
- How to bring up the application when `run:` checks require a live server or service.
- `setup`: Executed before start (e.g. database seed).
- `start`: Launched in the background.
- `ready`: Polled until it exits 0 before checks execute.
- `stop`: Optional shutdown command (otherwise the process group is terminated).
- `login`: Helpful credentials or tokens for human or automated testing.

### 4. `## Blind spots`
- Things that cannot be tested locally or are deliberately stubbed.
- A green run prints these so readers know what is untested.
