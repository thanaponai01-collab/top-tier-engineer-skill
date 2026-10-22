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

- Zero-test replays meet no expectation | proven
  - `run_replay` in `evals/grade.py` fails any replay whose output says no tests ran
    (`Ran 0 tests` / `no tests ran`), for `expect: pass` and `expect: fail` alike.
  - Rejection before the fix: on Python 3.11, `unittest discover` exits 0 with no tests, so
    `test_deleting_every_test_does_not_pass` failed (`check-passes-on-correct-code` was met);
    the new `test_a_replay_that_ran_no_tests_meets_neither_expectation` failed against the old grader.
  - Full proof: `python -m unittest discover tests` → `Ran 373 tests`, `OK (skipped=1)` (Python 3.11.9).
  - `git diff --check` passed.

- The lazy path is the correct path | proven | commit: The lazy path is the correct path
  - `verify.py assess` (one read-only call), `ANSWER DRAFT` with `[[fill: ...]]` slots, `answer-check`
    fixes and `ADD THESE LINES`, `ANSWER UNFILLED`, `gaps.survived`, runnable `NEXT` paths, short
    passing `advance` steps, SKILL.md rewritten as a router (body 6.9 KB → 4.9 KB).
  - Rejection before implementation: `tests/test_agent_path.py` → 15 of 18 failed/errored against the
    old helper and SKILL.md (no `assess`, no draft, no fixes, body 98 lines).
  - Fixture check: `assess` on `fake-check-and-decoy` (no `path:`) now prints `UNCOVERED line 4 …
    still passed` on `discount.py`; before, the three-command path mutated nothing there.
  - Review: `report --json` must equal `status --json`, so the draft stays text-only.
  - Full proof: `python -m unittest discover tests` → `Ran 392 tests`, `OK (skipped=1)` (Python 3.11.9).
  - `git diff --check` passed.

## Next
- Pay for an eval subset (`fake-check-and-decoy`, `green-with-unverified`, `teammate-loosened-check`)
  to measure turns and cost against the 1.18 numbers in `work/verify-loop-design.md`.
- Then add `max_turns`/`max_cost` and a helper-source-read failure to `grade.py` from that data.
- Release remains separate.
