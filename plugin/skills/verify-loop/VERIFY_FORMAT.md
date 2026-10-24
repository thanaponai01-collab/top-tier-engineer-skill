# VERIFY.md Reference & Schema

`VERIFY.md` lives at the repo root. It maps each feature in the codebase to runnable commands that prove it works.

## Format Overview

```markdown
require: challenge
include: packages/auth/VERIFY.md

## Feature Name
- path: src/feature/
- test: `python -m pytest tests/test_feature.py -q`
- run: `python scripts/smoke_driver.py`
- oracle: SPEC.md, data/feature_cases.json, scripts/smoke_driver.py
- schema: `python scripts/compliance.py schema schemas/feat.json out/feat.json --strict`
- privacy: `python scripts/compliance.py privacy out/`
- fail-signal: expected status 200, got 500
- fail-proof: changed the return status, test went red, reverted
- fresh: 3

## Journey: Complete Flow
- features: Feature A, Feature B
- test: `python -m pytest tests/test_flow.py -q`
- fail-signal: expected completed order, got pending
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
- Each bullet is `kind: <command>`, `fail-proof: <text>`, `oracle: <files>` or `fresh: <runs>`.
- `path:` lists the product files or folders the feature covers. It does four jobs: `--affected`
  selects the feature when they change, `challenge --auto` mutates them when no FILE is given, a
  failure receipt counts only if the files differed inside it when the check went red (see
  `fail-proof:`), and `run` measures the feature's `test:` checks against them. If every check passes without calling a
  function in those `.py` files (an import alone does not count), the feature is `HOLLOW` and the run
  is red: the check loads no cases, skips, or tests a copy of the logic. Without `path:` the product
  is the non-test repo code the checks imported: `HOLLOW` when they import it but call none of it,
  and one call anywhere clears it, so `path:` is the sharper fence. Not judged: features with a
  `run:` or other non-`test:` check, any recipe with a `## Run` section (the app runs outside the
  measurement), cached passes, non-Python checks and modules that define no function.
- A check passes when its command exits 0.
- `fail-proof:` explains the controlled wrong state and intended failure signal. Strict runs also
  require a retained failing command/output for the current check hashes; a sentence alone fails.
  The run records every file's hash when a check went red (once per run, shared by its receipts). Once the check passes again it
  counts only if a product file differed then: one inside `path:` when the feature has one, else
  any file that is not a test, a check, an oracle or Markdown. A red on the same files that pass
  now came from the environment (`PROOF NOT FROM PRODUCT`). A caught `challenge` mutation always
  counts. Receipts made before 1.18.0 carry no file hashes: prove again.
- `fail-signal:` is a literal behavioral rejection message matched against retained output.
  Missing dependencies, syntax errors and startup failures cannot prove product behavior. Declare
  the signal before the negative run; changing it invalidates earlier evidence. A signal that is
  only runner boilerplate (`FAILED`, `Error`, `AssertionError`, `Traceback`, `exit code 1`, `not
  ok`) is `WEAK SIGNAL` and proves nothing: once those words and exit codes are removed, a number or
  a word of three letters or more must remain (`expected total 189`, `refund credit mismatch`).
- `oracle:` lists comma-separated repo-relative spec, fixture and helper files to freeze, alongside
  automatically frozen tests, directly named script paths and commands. List imported helpers
  and expectation data explicitly; dependency discovery is not exhaustive. Missing files fail. Keep implementation files out.
- `fresh: N` (1-20) guards against product code that special-cases the inputs its check was
  written with (`if (credit, amount) == (100, 50): return 150`), which every mutation on that line
  and the `HOLLOW` gate both miss. The feature's checks first run with `VERIFY_SEED` unset: their
  own cases. When all pass, `run` repeats them N times, each with a random `VERIFY_SEED`, and the
  check draws fresh cases from it, with expected values from the spec, never from the product. A
  red fresh run is `OVERFIT` and keeps the run red; it prints the seed, so `VERIFY_SEED=<seed>
  <command>` reproduces it. Fix the product, not the check. `SEED UNUSED` (also red) means no test
  file, script, oracle or command of the feature names `VERIFY_SEED`, so a fresh run would only
  repeat the own cases. Frozen by `baseline`: removing `fresh:` is `CHECK CHANGED`, and a
  re-baseline that lowers N needs review. Not run inside `challenge` copies. `require: fresh` makes
  it mandatory.
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
- For a build-sensitive service, make the doctor identify the artifact actually loaded by the
  process. Compare a running source/build content digest and material configuration with the
  expected checkout, including uncommitted source, resolved flags, roles and mocked boundaries.
  HEAD is provenance, not an identity for dirty source. Keep owner/PID checks where needed to
  distinguish the intended instance. Report the expected and observed values for each mismatch;
  health or PID alone does not prove artifact identity. Record the check in the affected VERIFY.md
  section with its oracle, literal fail-signal and observed fail-proof, then run it through verify.py
  so the output remains in the run receipt. Prove both sides: unchanged current identity passes, and
  a healthy old process on the expected port is rejected after a source or runtime-contract change.
  Exercise a dirty-source change without committing it so the test holds HEAD constant.
- `stop`: Optional shutdown command (otherwise the process group is terminated).
- `login`: Login/role instructions; refer to secrets by location rather than recording their values.

### 4. `## Blind spots`
- Things that cannot be tested locally or are deliberately stubbed.
- A green run prints these so readers know what is untested.
- Product source no feature reaches (by `path:`, a command, an `oracle:`, the recorded coverage map
  or an import from a mapped test) is `UNMAPPED` and keeps `run --strict` red. A blind-spot line
  that names the file or its folder (`` `legacy/` is frozen and untested ``) excuses it. Tests,
  config files (`setup.py`, `*.config.js`), hidden folders and Python files that define no function
  or class are not product.

### 5. `include: <path>`
- A top-level line (outside any section) that reads another recipe in place; the path is from the
  repo root, written bare (`include: verify/billing.md`), nothing else on the line.
- Past about 150 lines, split by area: `VERIFY.md` keeps `## Run`, `## Blind spots` and one
  `include:` per area, and each area's sections move to `verify/<area>.md` verbatim.
  Every verify.py command that reads the recipe follows the includes, so the split changes no verdict.

### 6. `require: <words>`
- A top-level line (outside any section). `require: challenge` makes `run --strict` stay red
  (`UNCHALLENGED`) until `verify.py challenge` has caught a mutation for the current checks.
  `verify.py init` writes it. It is frozen by `baseline`: removing it later is `CHECK CHANGED`.
- `require: independent` makes `run --strict` stay red (`NOT INDEPENDENT`) for every check whose
  `baseline` was run by the same `VERIFY_AGENT` as the strict run, or by an unnamed agent. `baseline`
  records who froze each check (`frozen_by`); a later baseline by someone else keeps the original
  freezer of an unchanged check. Words combine: `require: challenge, independent`.
- `require: fresh` makes `run --strict` stay red (`NO FRESH INPUTS`) for every feature with checks,
  journeys aside, that declares no `fresh: N`. Use it when a claim covers a range of inputs
  (any amount, any percentage) that fixed cases cannot.

## Completion

`run --strict` requires a baseline and rejects failed checks, unverified features, missing rejection evidence, orphan
test files, `UNMAPPED` product files and `LOOSENED` tests. Name each test file or its folder in a command so the map can attribute it. Strict
green covers mapped claims only; it does not prove the feature inventory is complete.

`status` requires the last whole run to be strict, green and unchanged by content. A non-strict
pass is `partial`; a failed strict run stays red. Output tails and rejection receipts remain in
.verify-state.json after app teardown. Capture larger artifacts separately and redact secrets.

A changed or removed frozen check, or a changed `fail-signal:`, re-freezes only with
`baseline --reviewed-by <name> --reason <why>`; added checks and `## Run` repairs need no review.

Before any baseline, `LOOSENED` covers the same ground from git: for each test file a command
names, the last 30 commits that touched it and any uncommitted edit are compared test by test. A
test that was removed or skipped, lost assertions, lost an exact assertion (`assertEqual` became
`assertAlmostEqual(..., delta=2)` or `assertTrue`, `toBe` became `toBeCloseTo`) or kept its
exact assertions but changed their expected literals is listed with the commit, author and
subject. `baseline` refuses while any is listed; `--reviewed-by --reason` records them as reviewed.
This makes a self-approved change visible, not impossible: the state file is local and editable,
so committed checks under review rules and the `ci` mode remain the independent guard.

.verify-state.json is sealed with a content hash on every write. A file edited by hand reads as
`STATE FORGED` on run and `tampered` on status until it is deleted and verification starts over.
The seal has no secret, so it catches careless or naive edits, not a writer who recomputes it;
independently owned CI is the boundary for that.

Saves are atomic and locked, and concurrent saves merge. `VERIFY_AGENT=<name>` keeps an agent's
loop memory in `.verify-state.<name>.json` while the baseline, re-baselines and receipts stay in
.verify-state.json; see [helper commands](references/helpers.md). Gitignore `.verify-state*`.
Commands run through the shell like a Makefile: run recipes only from a repo you trust.
