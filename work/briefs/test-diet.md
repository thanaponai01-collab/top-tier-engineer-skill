# Test diet: tests shorter to read and faster to run, with nothing lost

## Intent
<!-- purpose -->The user asked to point the "find all of the implicit state machines" lens at their
tests, because tests feel too long. Long tests hide structures nobody declared: the same path
through the app replayed in many tests just to reach the state one of them checks (make user,
verify, add to cart, pay, then test refunds), the same setup block copied by hand, tests that are
slow because of a sleep, the network or setup rebuilt each time, and tests that only check what a
mock was told. Making tests shorter is easy; doing it without losing a bug the old suite would have
caught is the hard part, and a reader cannot see that loss. The skill earns its place only if every
shortening is held by a check that the slimmer suite still catches every planted bug the old one
caught.
<!-- end state -->The user types one word and gets their tests shorter and faster, with numbers:
lines, tests, seconds and planted bugs caught, before and after. `python
plugin/skills/test-diet/scripts/diet.py <repo>` lists repeated setup (with the calls it replays),
slow tests with their causes, and mock-only tests; `--run CMD` records the tests, their times and
which planted bugs (mutants of the code the tests import) they catch; `--done` refuses while a lead
is neither handled nor kept with a reason, a handled repeat is still repeated, a handled slow test
is not faster, a planted bug caught before is missed now, app code changed, a test that passed
fails, or the tests got longer or slower; then it writes `.diet/REPORT.md` and prints
`DIET: done`.
<!-- done when -->Every condition under Acceptance passes, the skill is tried on a fixture with the
result reported honestly, the skill is registered like its siblings, and the full suite passes.

## Context
<!-- grounding -->
- The user does not read code. The answer is the numbers before and after, then plain words.
- "Too long" means long to read and long to run; both are in scope.
- Deleting or merging tests is where the danger is. Fewer tests is allowed; fewer bugs caught is
  not, so the gate is planted bugs, not test count.
- Past ports show plain Opus often ties on finding. Gains came where a script caught what the agent
  skipped, so every rule here is a check the helper runs.
- A slow test whose cause is in the app (a retry sleep) cannot be fixed from the tests; it is kept
  with that reason, since this skill does not change the app.
<!-- scope -->A new manual-only skill `plugin/skills/test-diet/` (SKILL.md and `scripts/diet.py`,
stdlib only), state in `.diet/`. Python tests are read by AST and timed per test (unittest through
the helper's own runner, pytest through `--durations`); other test files get text-level repeated
blocks only, and planted bugs are Python only. Also `tests/test_diet.py` and registration in
CLAUDE.md, both plugin manifests and CHANGELOG.md.
<!-- non-goals -->
- Changing app code: the skill only changes test files (tests folders, `test_*` files, conftest).
- Tests that cannot fail: verify-loop's job.
- Order dependence and flakiness: not checked; named as not checked.
- Hooks, linters or CI rules: the user cannot maintain them.

## Guardrails
<!-- constraints -->
- One helper, `D`, three commands.
  - `D <repo> [paths]` writes `.diet/candidates.md`: `setup:<id>` blocks of three or more
    statements repeated in two or more tests (names and literals normalized), with the calls they
    replay; `slow:<test>` tests at 0.25 s or more once timed, and tests whose body sleeps, opens the
    network or starts a process; `mock:<test>` tests whose only assertions are on mocks.
  - `D --run CMD [--mutants N]` records the suite result, per-test times, test lines, a hash of
    every app file, and which of N planted bugs in the app files the tests import the suite catches.
  - `D --done` reads `.diet/plan.json` (`changes` with `covers`, `what`, `at`; `kept` with
    `candidate`, `why`) and refuses when: a lead is neither covered nor kept with a reason; a
    covered setup is still in two or more tests; a covered slow test still exists and is not at
    least twice as fast or under 0.1 s; a covered mock-only test still checks only mocks; a planted
    bug caught before is missed now; an app file changed, appeared or went away; the tests passed
    before and fail now; test lines grew; the suite is slower by more than a quarter plus half a
    second. Otherwise it writes `.diet/REPORT.md` and prints `DIET: done`.
- SKILL.md body is at most 3,000 characters.
<!-- invariants -->
- App files are never changed.
- Every planted bug the old suite caught is caught by the new one.
<!-- escalation -->A slow test caused by app code is reported, not fixed. The skill commits nothing.

## Freedom
<!-- latitude -->How the agent shortens tests (fixtures, builders, a helper that starts in the
target state, parametrize, merging or deleting), which leads it keeps, and the order of the work.

## Gates
<!-- precondition -->Stage 1, find: a repo with tests.
<!-- postcondition -->Leads are listed and the suite, its times and its caught planted bugs are
recorded before any change.
<!-- evidence -->`python -m unittest tests/test_diet.py`
<!-- precondition -->Stage 2, done: the record and `.diet/plan.json` exist.
<!-- postcondition -->Every lead is handled or kept, nothing caught before is missed, the app is
untouched, and the tests are no longer and no slower.
<!-- evidence -->`.diet/REPORT.md` and `python -m unittest tests/test_diet.py`

## Output
<!-- deliverable -->`plugin/skills/test-diet/` with its helper, plus the release bookkeeping.
<!-- acceptance -->`tests/test_diet.py` holds every rule above. Each rule, broken in the helper,
turns at least one of its tests red.
<!-- verification -->`python -m unittest discover tests`
