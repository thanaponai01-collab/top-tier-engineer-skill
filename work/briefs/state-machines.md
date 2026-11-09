# State machines: find the ones the code never declared

## Intent
<!-- purpose -->The user asked for a skill behind the prompt "find all of the implicit state machines
in my app". Most apps hold state machines nobody wrote down: a status string set in six files and
checked in twelve, booleans that only make sense in some combinations (`printing` and `error` both
true), a field whose `None` means "not yet". The bugs live in the gaps: a value that is checked but
never set (a typo, or a renamed state), a combination of flags that should be impossible but is
reachable, a state with no way out, a transition that skips its guard. It began (1.46.0) with a
helper script that listed every write and check; the eval tied plain Opus at 1.4-2.4x cost, so on
2026-11-08 it became a saved prompt in plain words (CLAUDE.md, "How a skill is written") and the
script and its tests were removed.
<!-- end state -->The user types one word and gets every implicit state machine drawn as a picture
with its states and transitions, the bugs in plain words, each bug held by a test that failed on the
code as it was, and the bugs they asked to fix fixed without breaking anything. `SKILL.md` says the
goal, what done looks like, what to avoid and the fixed answer block; the method is the model's.
<!-- done when -->`SKILL.md` is about one page of plain prose with that answer block, nothing names
the removed script, and the full suite passes.

## Context
<!-- grounding -->
- The user does not read code. Each machine is shown as a diagram, bugs in plain words first,
  `file:line` second.
- A string value compared in one file but written nowhere is the easiest bug to skim past by eye;
  done names it explicitly.
- Two booleans set together are not always a machine: independent preferences (email on, SMS on)
  allow every combination.
<!-- scope -->The manual-only skill `plugin/skills/state-machines/SKILL.md`, its eval cases and its
registration in CLAUDE.md and both plugin manifests.
<!-- non-goals -->
- Rewriting the app around a state-machine library or an enum: the user can ask for that later.
- Proving a machine correct in general: formal-check's job.
- Hooks, linters or CI rules: the user cannot maintain them.

## Guardrails
<!-- constraints -->
- Every write and check of a status field or flag is accounted for by `file:line`; each value
  checked but never set and each state nothing leaves gets a verdict.
- Each bug is proven by a test that fails on the code as it was, not on an import error.
- Each machine is drawn as a diagram.
<!-- invariants -->
- No test that passed before fails after.
<!-- escalation -->Bugs the user did not ask to fix are reported, not fixed. The skill commits
nothing.

## Freedom
<!-- latitude -->How the agent reads the code, which fields it groups into one machine, which leads
it sets aside, how it writes each test and each fix, and the order of the work.

## Gates
<!-- precondition -->A repo.
<!-- postcondition -->The answer block: each machine with its states, each bug fixed or open with
its proof, what looked wrong and is not, and the test counts before and after.
<!-- evidence -->The eval cases `evals/cases/state-machines-*`.

## Output
<!-- deliverable -->`plugin/skills/state-machines/SKILL.md` and its eval cases.
<!-- acceptance -->`tests/test_spec.py` passes on this brief, and the eval cases are judged by
outcome in both arms.
<!-- verification -->`python -m unittest discover tests`
