# Test diet: tests shorter to read and faster to run, with nothing lost

## Intent
<!-- purpose -->The user asked to point the "find all of the implicit state machines" lens at their
tests, because tests feel too long. Long tests hide structures nobody declared: the same path
through the app replayed in many tests just to reach the state one of them checks (make user,
verify, add to cart, pay, then test refunds), the same setup block copied by hand, tests that are
slow because of a sleep, the network or setup rebuilt each time, and tests that only check what a
mock was told. Making tests shorter is easy; doing it without losing a bug the old suite would have
caught is the hard part, and a reader cannot see that loss. It began (1.47.0) with a helper script
that listed leads, timed tests, planted bugs and refused a bad diet; no eval showed it beat plain
Opus, so on 2026-11-09 it became a saved prompt in plain words (CLAUDE.md, "How a skill is
written") and the script and its tests were removed.
<!-- end state -->The user types one word and gets their tests shorter and faster, with numbers:
tests, lines, seconds and planted bugs caught, before and after. `SKILL.md` says the goal, what
done looks like, what to avoid and the fixed answer block; the method is the model's.
<!-- done when -->`SKILL.md` is about one page of plain prose with that answer block, nothing names
the removed script, and the full suite passes.

## Context
<!-- grounding -->
- The user does not read code. The answer is the numbers before and after, then plain words.
- "Too long" means long to read and long to run; both are in scope.
- Deleting or merging tests is where the danger is. Fewer tests is allowed; fewer bugs caught is
  not, so the measure is planted bugs, not test count.
- A slow test whose cause is in the app (a retry sleep) cannot be fixed from the tests; it is kept
  with that reason, since this skill does not change the app.
- Files git ignores (caches a test run writes) are not app code; their changing is not an app
  change.
<!-- scope -->The manual-only skill `plugin/skills/test-diet/SKILL.md` and its registration in
CLAUDE.md and both plugin manifests.
<!-- non-goals -->
- Changing app code: the skill only changes test files (tests folders, `test_*` files, conftest).
- Tests that cannot fail: verify-loop's job.
- Order dependence and flakiness: not checked; named as not checked.
- Hooks, linters or CI rules: the user cannot maintain them.

## Guardrails
<!-- constraints -->
- The old suite's tests, lines, times and the planted bugs it catches are recorded before any
  change.
- Every repeated setup, slow test and mock-only test found is slimmed or kept with a reason.
<!-- invariants -->
- App files are never changed.
- The new suite passes, is no longer and no slower, and catches every planted bug the old one
  caught.
<!-- escalation -->A slow test caused by app code is reported, not fixed. The skill commits nothing.

## Freedom
<!-- latitude -->How the agent finds leads, plants bugs and shortens tests (fixtures, builders, a
helper that starts in the target state, parametrize, merging or deleting), which leads it keeps,
and the order of the work.

## Gates
<!-- precondition -->A repo with tests.
<!-- postcondition -->The answer block: numbers before and after, planted bugs caught before and
after, what changed, what was kept and why, what was not checked.
<!-- evidence -->`python -m unittest tests/test_spec.py`

## Output
<!-- deliverable -->`plugin/skills/test-diet/SKILL.md`.
<!-- acceptance -->`tests/test_spec.py` passes on this brief; an eval case is still to be built.
<!-- verification -->`python -m unittest discover tests`
