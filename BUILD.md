# Build record

- Automatic progression | proven | commit: Add bounded automatic verification progression
  - Entry point: `verify.py advance <repo> --json`.
  - Rejection before implementation: 10 CLI tests failed because `advance` was absent;
    retained output: `/tmp/verify-advance-before.txt`.
  - Focused proof: `PATH="/tmp/verify-advance-venv/bin:$PATH" python -m unittest discover -s tests -p 'test_advance.py'` → `Ran 16 tests`, `OK`.
  - Full proof: `PATH="/Users/teamporary4/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin:$PATH" python3 -m unittest discover tests` → `Ran 369 tests in 90.927s`, `OK`.
  - Full output: `/tmp/verify-advance-suite-modern.txt` (Python 3.12.14).
  - `git diff --check` passed; context handoff check: zero structural gaps.
  - Python 3.9 run exposed existing CI archive API incompatibility and an eval behavior difference;
    the supported test evidence for this slice is the passing Python 3.12 run.
  - Review tightened input validation to cover decision stops as well as executable steps.

- File handle resource and UTF-8 hygiene | proven
  - Cleaned up unmanaged file handles and missing UTF-8 encodings across tests, evals and scripts.
  - Focused proof: `python -W error::ResourceWarning -m unittest discover -s tests -p 'test_caller_answer.py'` → `Ran 12 tests`, `OK`.
  - Focused proof: `python -W error::ResourceWarning -m unittest discover -s tests -p 'test_gates.py'` → `Ran 27 tests`, `OK`.
  - Zero unmanaged `open()` calls across the repository.
  - `git diff --check` passed.

- Advance promotion in SKILL.md | proven
  - Primary mechanical progression driven by `verify.py advance <repo> --json`.
  - Removes redundant manual baseline/run steps from the agent's task table; preserves decision steps.
  - Focused proof: `python -m unittest discover -s tests -p 'test_advance.py'` → `Ran 16 tests`, `OK`.
  - `git diff --check` passed.

- Challenge mutation passivity reporting | proven
  - In `challenge --auto`, report that an uncovered or surviving mutation "still passed" (e.g. `breaking <before> (-> <after>) still passed`), making test passivity explicit in tool output.
  - Focused proof: `python -m unittest discover -s tests -p 'test_hollow.py'` → `Ran 20 tests`, `OK`.
  - Reference grade verification: `python evals/grade.py verify-loop-fake-check-and-decoy --report ...` → `3/3 found, score 1.00`.
  - `git diff --check` passed.

- CI fresh proof eval phrase match inflection coverage | proven
  - Broadened phrase matcher inflection coverage in ci-fresh-proof eval to accept natural variants of unbacked state rejection (e.g. "ignores", "excluded", "didn't trust", "left out").
  - Focused proof: `python -m unittest discover -s tests -p 'test_evals.py'` → `Ran 37 tests`, `OK`.
  - Grade verification: `python evals/grade.py verify-loop-ci-fresh-proof --report ...` → `2/2 found, score 1.00`.
  - `git diff --check` passed.

- Claude Code's own /verify (1.20.0) | proven
  - Generated verify skill gets `## Before a commit` (`verify.py run . --affected`), enforced by
    `skill-check`/`maintain`; `scaffold-skill --adopt` completes a recipe the bundled `/verify` recorded.
  - Rejection before implementation: the 5 new tests in `test_caller_answer.py` failed (4 FAIL,
    1 ERROR) with `create.py`/`verify.py` stashed.
  - A first version of the gate passed when the command was swapped for `--strict` (prose also said
    `--affected`); the gate now requires `verify.py run <repo> --affected` literally.
  - Full proof: `python -m unittest discover tests` on Python 3.13, Windows.

- Fresh inputs: OVERFIT (1.21.0) | proven
  - `- fresh: N` re-runs a feature's passing checks under N random `VERIFY_SEED` values; a product
    that passes its own cases and fails a fresh one is `OVERFIT` (red, `fix` step). `SEED UNUSED`
    when no check file reads the seed; a bad count is `BROKEN`; `fresh:` is frozen by `baseline`.
  - Rejection before implementation: 9 of the 11 tests in `tests/test_fresh.py` failed; `fresh: 3`
    was run as a shell command (`'3' is not recognized`).
  - Focused proof: `python -m unittest discover -s tests -p test_fresh.py` → `Ran 11 tests`, `OK`.
  - Full proof: `python -m unittest discover tests` → `Ran 387 tests in 277.838s`, `OK (skipped=1)`,
    Python 3.13, Windows.

## Next
1.21.0 is uncommitted on `verify-loop-only`. Open: `require: fresh` (strict red for a feature
without `fresh:`) and an eval case for a special-cased product are not built.
