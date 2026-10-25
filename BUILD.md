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

- Assess says what it saw | proven
  - The `assess` draft and `REJECTED` line name what the survey caught per feature (`surveyed` in
    the answer JSON) and say that a catch is not a fail-proof receipt. Before, they said nothing had
    been seen red after the survey caught every wrong result. On `compound-assess` that pointed at
    the healthy-shipping decoy (6/6 caught).
  - `assess` points a partial verdict at `advance` instead of `run --strict`, and prints no `SWARM:`
    line. A read-only question doesn't start helper agents.
  - Rejection before implementation: `tests/test_agent_path.py` `AssessSaysWhatItSaw` → 2 of 2 failed.
  - Full proof: `python -m unittest discover tests` → `Ran 409 tests`, `OK (skipped=1)` (Python 3.11.9).

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

- Survey score in report, require: fresh, overfit eval (1.22.0) | proven
  - `report` prints `SURVEY` for the last `challenge --auto` on the current checks and tree (kept in
    the cache, not .verify-state.json); `require: fresh` makes strict red with `NO FRESH INPUTS`.
  - Rejection before implementation: 3 of 4 tests in `tests/test_survey_report.py` and 2 of the 4
    new `RequireFresh` tests in `tests/test_fresh.py` failed.
  - The first full run caught a regression: `test_challenge` requires a survey to leave no
    .verify-state.json, so the score moved to the cache instead of the test being changed.
  - Full proof: `python -m unittest discover tests` → `Ran 395 tests in 241.431s`, `OK (skipped=1)`,
    Python 3.13, Windows.
  - Eval `verify-loop-special-cased-product`, 3 tries per arm: 3/3 without, 3/3 with; $0.10 vs
    $0.17 a try; no try used `fresh:`. Results in `evals/results/2026-10-25-special-cased/`.

- Trigger eval and description (1.23.0) | proven
  - `python evals/trigger.py`: 26 prompts, train/test split, isolation checked per try (0 invalid
    in 160 tries). Baseline Opus 5.5 fired on 9/26 wanted, 0/26 unwanted.
  - Candidate A (intents) train 12/14; missed "tests pass but test nothing". Candidate B adds the
    weak-tests intent: train 14/14, held-out 10/12, Sonnet 11/13, false fires 0 throughout.
  - Rejection: `test_live_description_is_the_measured_one` failed on an unmeasured description edit,
    passed once restored. Full proof: `python -m unittest discover tests` -> `Ran 407 tests`,
    `OK (skipped=1)`, Python 3.13, Windows.
  - Results in `evals/results/trigger-2026-10-25-*`; cost about $18.

- Merge of the Oct 22 agent-path line with 1.20.0-1.23.0 | proven
  - `report` keeps the agent-path layout (`ANSWER DRAFT`, `gates.gap_rows`, assess `surveyed`) and
    the 1.22.0 cache `SURVEY` lines; `no fresh inputs` joins `gates.GAP_LABELS`.
  - SKILL.md keeps the router body; `OVERFIT` stays in the `fix` row, `fresh:` lives in
    VERIFY_FORMAT.md, body 4,955 of 5,000 characters.
  - Description cap 400 -> 800: a 384-character candidate scored held-out 8/12 (Sonnet 2/6) against
    10/12 (4/6) for the measured one; results in `evals/results/trigger-2026-10-25-cand-{c,d}-*`.
  - `compound-advance` reference solution read stale on Windows (autocrlf rewrote its .md files
    under a byte-hashed state); `.gitattributes` pins `reference/solution/**` to LF.
  - Full proof: `python -m unittest discover tests` -> `Ran 444 tests`, `OK (skipped=1)`, Python 3.13, Windows.

- feature-map skill shipped in the plugin (1.24.0) | traced
  - Copied from `origin/main` unchanged; `features.py --help` runs; no feature-map tests or eval
    here yet. Full proof: `python -m unittest discover tests` -> `Ran 444 tests`, `OK (skipped=1)`.

- feature-map mechanics and evals (1.26.0) | proven (mechanics) / helps on narrow follow-ups (eval)
  - `features.py` gains `prove` (receipts, `--copy`, `--file`, `--again`), `check --rerun`, a
    vendored `.features/features.py`, `## Not features`, trace-start check, quoted CLI anchors,
    `failing` label, `unannounced`; verify-loop link only when VERIFY.md exists.
  - Full proof: `python -m unittest discover tests` -> `Ran 487 tests`, `OK (skipped=1)`; feature-map 43.
  - Eval, 3 tries per arm on 5 cases (up to a 133-command CLI): plain Opus 5.5 matches the skill on every case and costs
    about half; results in `evals/results/2026-10-25-feature-map-*`. Renamed-receipt pruning
    landed after the last batch and is unmeasured.
  - Where it helps (`feature-map-alarm-on-narrow-task`): a later session asked only to document a
    rename raised 8 of 9 unmentioned runtime breaks with the map's `check --rerun`, plain Opus 0 of
    9 (2/3 vs 0/3 pass), at about 2.3x the cost. Results in `evals/results/2026-10-25-feature-map-alarm`.

- latent-audit as a checkpoint (1.27.0) | proven (mechanics) / no gain over plain Opus (eval)
  - `tests/test_graph_audit.py`: the 6 tests from main plus 10 for `--try-delete` verdicts and map
    roots (a by-name job is LIVE; tests-only is `weak`; the map's recorded runs catch a live deletion).
  - Evals in `evals/results/2026-10-25-latent-*`: without 3/3 + 3/3; with 3/3 + 3/3 after the
    SKILL.md wording fix (`-with-3` and `-with`), about 1.3x the cost.

- latent-audit as three stages (1.28.0) | proven (mechanics) / costs 1.3-1.6x plain Opus, accounts for every dead file (eval)
  - Stages from a trace of plain Opus: snapshot with an import hook, in-place delete + rerun,
    account for the rest. `tests/test_graph_audit.py` 28 tests; 3 mutations each caught.
  - Eval `evals/results/2026-10-25-latent-audit-stages`: 6/6; cleanup session $0.28 vs $0.17 on 25
    suspects. Remaining overhead is protocol calls (read SKILL, snapshot, gate rounds, verdict file).
  - Template for the other skills if it holds up.

- wire-check as three stages (1.29.0) | proven (mechanics) / no gain over plain Opus, 2.6x cost (eval)
  - `scripts/wire.py`: call-trace snapshot, function-level account, keep stage tied to feature-map
    and verify-loop receipts. `tests/test_wire.py` 10 tests; 6 mutations each caught.
  - Baseline `evals/results/2026-10-25-wire-check-baseline`: plain 8/9, copied skill 9/9.
  - Rebuild `evals/results/2026-10-25-wire-check-rebuild`: 15/15 both arms, $0.44 vs $0.17 a try;
    the too-big and narrow-follow-up cases did not separate the arms.

- feature-map as three stages (1.30.0) | proven (mechanics) / ties plain Opus on a general map, 2.2x cost; wins the narrow follow-up 8/9 vs 0/3 (eval)
  - `features.py gate` (Inventory, Run, Hand off), `prove --serve/--request`, controls proven through
    their route. `tests/test_features.py` 51 tests.
  - General case `evals/results/2026-10-25-fm-general-{base,rebuild,rebuild2}`: 9/9 every try in both
    arms; mapping session $0.26 plain, $0.91 -> $0.57 with the skill. Session 2 costs the same: a fresh
    agent re-reads the code whether or not a map is there, so the map pays only once code moves.
  - Alarm `evals/results/2026-10-25-fm-alarm-{rebuild,rebuild-b,slim}`: 8/9; the miss left no passing rating receipt.
  - SKILL.md is goal + steps (done when, checked by) + tools; `-slim` batches match the longer doc.

- debug-protocol as three stages (1.31.0) | proven (mechanics) / helps on the two-way proof (eval)
  - `scripts/debug.py`: reproduce (code kept as reproduced), prove (only the cause replaced, rerun),
    leave (tree as it was, or a fix at the cause held by a check that fails with it put back).
    `tests/test_debug.py` 14 tests; 8 disabled guards each caught.
  - Plain traces `evals/results/2026-10-25-debug-protocol-baseline` and `-plain-2`; rebuild
    `evals/results/2026-10-25-debug-protocol-rebuild` (+ `-rebuild-2`, skill arm after the VERIFY.md
    message): distant-cause 3/3 vs plain 0/3 ($0.13 vs $0.07), regression-proof 3/3 both ($0.18 vs $0.14).
  - Not covered: a hang, a flaky failure, a cause outside one file's lines (data, environment, timing).

- structure-gate as three stages (1.32.0) | proven (mechanics) / helps on code no tool can reach, ties on an ordinary app (eval)
  - `scripts/structure.py --gate`: measure (share a parser entered), account (a counted reading or
    UNKNOWN per unentered region, a cost per finding, in `.structure/notes.md`), answer (verdict the
    measurement allows). `tests/test_structure.py` 21 tests; 23 disabled guards each caught.
  - Baseline `evals/results/2026-10-25-structure-gate-baseline`: plain 0/3 opaque, 3/3 general; copied skill 3/3 opaque.
  - Rebuild `evals/results/2026-10-25-structure-gate-rebuild`: opaque 3/3 vs 0/3 ($0.17 vs $0.09),
    general 3/3 vs 2/3 ($0.21 vs $0.17). Plain Opus finds every tangle by reading; what it lacks is the denominator.
  - Not covered: a repo too big to read, non-Python depth (JS gets length and copies only), the baseline ratchet in CI.

- threat-model as three stages (1.33.0) | proven (mechanics) / ties plain Opus on all five cases at about 2x cost (eval)
  - `scripts/threat.py`: doors (a scan of route tables, registering decorators, handlers and scripts),
    attack (each door entered by a kept attack in `tests/test_*.py`, or `out:` with a reason that does
    not lean on a defense), hold (attacks rerun; a fix shuts each open one and is seen failing with the
    change put back). `tests/test_threat.py` 19 tests; 16 disabled guards each caught.
  - Plain `evals/results/2026-10-25-threat-model-baseline` + `-outlive-plain`: 15/15 ($0.11-0.35).
    Main's skill as copied `-copied`: 6/6. Rebuild `-rebuild`: 15/15 ($0.22-0.64, mean $0.40 vs $0.20).
  - Plain Opus reads the whole small app, probes every suspicion and finds each planted abuse, including
    a guard that reads as applied and an unmentioned teammate change during an unrelated task. What it
    never leaves is the attacks: its probes are deleted. The skill leaves them in the suite.
  - Not covered: an app too big to read in one call (the case the doors count is for), and open attacks
    kept as plain tests leave the suite red until fixed (a later session saw 8-10 failures).

- evolve-maintain as three stages (1.34.0) | proven (mechanics) / ties plain Opus on both cases (eval)
  - `scripts/evolve.py`: before (`E` keeps the tree in `.evolve/before/`; `E --run CMD` records what a
    command prints and writes, always on the kept tree, refused if it varies or enters no repo code),
    reach (every function, module body or config line that reads a name the change touched is entered
    by a recorded run under a call tracer and an open() audit hook, or has `out:` that does not claim a
    run), hold (every run reruns on the changed tree; output or written files that differ are fixed or
    marked `intended:`). `tests/test_evolve.py` 20 tests; 19 disabled guards each caught.
  - New case `evolve-maintain-distant-break`: cache `Order.total`; the obvious cache leaves a stale
    refund receipt and breaks backup/restore, suite green. Plus main's `evolve-maintain-hidden-caller`.
  - Baseline `evals/results/2026-10-26-evolve-baseline`: plain 6/6 ($0.14); main's skill as copied 5/6
    ($0.25; one try cached in the dashboard instead of `Order`). Rebuild `-evolve-rebuilt`: 6/6 ($0.23);
    one try read the helper's source after Git Bash rewrote `/v1/export` inside a run. Fixed
    (`MSYS_NO_PATHCONV`); `-evolve-rebuilt-pathfix` hidden-caller 3/3 ($0.19), no source reads.
  - Every rebuilt try reached `EVOLVE-GATE: done`. The gate only ever flagged differences the user asked
    for (v1 now 404s, a deleted v1 test): agents had named the distant breaks from reading, as plain Opus does.
  - Not covered: an app too big to read in one call, where the reader list and the reruns are what
    would find the break; callers outside the repo; non-Python readers beyond text lines.

## Next
1.20.0 to 1.24.0 are committed on `verify-loop-only`; GitHub main still ships top-tier-engineer
4.66.0, so installs get none of verify-loop. The held-out trigger miss "double-check the fix before
I merge" needs new train prompts in that shape before tuning, never the test prompt itself. The
overfit eval still shows no difference (see 1.22.0).
- Pay for an eval subset (`fake-check-and-decoy`, `green-with-unverified`, `teammate-loosened-check`)
  to measure turns and cost against the 1.18 numbers in `work/verify-loop-design.md`.
- Then add `max_turns`/`max_cost` and a helper-source-read failure to `grade.py` from that data.
- feature-map: it wins only when a later task is narrow (the alarm catches what nobody asked about);
  asked to verify everything, plain Opus ties it at about half the cost. Cut session-1 proving cost next.
- Release remains separate.
