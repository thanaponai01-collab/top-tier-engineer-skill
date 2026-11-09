# Cleanup: clear what agents leave behind

## Intent
<!-- purpose -->The user wants a skill that leaves a codebase the next agent can work in without
being misled. Agents leave things behind: dead code, orphaned files, `_v2`/`_old` copies,
duplicated helpers, two ways of doing one job, debug prints, commented-out code, silent failures,
stubs, and comments about past changes. The real danger in cleaning them is deleting something
that looked unused but was loaded by name. It cleans the mess; it does not reshape the building.
It began (1.42.0) with a helper script that listed candidates and refused done while tests got
worse; the eval tied plain Opus (3/3 vs 3/3, evals/results/2026-11-07-cleanup-plain), so on
2026-11-09 it became a saved prompt in plain words (CLAUDE.md, "How a skill is written") and the
script and its tests were removed.
<!-- end state -->The user types one word and gets a cleanup without explaining it again: the mess
removed or merged, what looked like mess but is used kept with a reason, behavior-changing finds
named, and a record in `.cleanup/` the next run compares against. `SKILL.md` says the goal, what
done looks like, what to avoid and the fixed answer block; the method is the model's.
<!-- done when -->`SKILL.md` is about one page of plain prose with that answer block, nothing names
the removed script, and the full suite passes.

## Context
<!-- grounding -->
- The user does not read code. The answer is plain words first, `file:line` second.
- The user cannot look after hooks, linters or CI rules, so none is installed. A record of each
  run replaces them.
- Fixing a silent failure, a stub or code that games a test changes what the program does. That is
  allowed when the answer names the change in behavior.
<!-- scope -->The manual-only skill `plugin/skills/cleanup/SKILL.md`, its eval case and its
registration in CLAUDE.md and both plugin manifests.
<!-- non-goals -->
- Hooks, linter configs, pre-commit or CI rules: the user cannot maintain them.
- Restructuring (splitting big files, moving modules, layers): untangle's and arch-design's job.
- Measuring complexity: structure-gate's job.
- Checks against one repeated mistake: mistake-proof's job.

## Guardrails
<!-- constraints -->
- Each piece of mess is listed by `file:line` and removed, merged, kept with a reason, or reported.
- Swallowed errors, stubs and hard-coded answers are named; a fix is allowed only when the answer
  says it changes behavior.
<!-- invariants -->
- No test that passed before fails after, and no fewer tests run.
- A deleted file's name is written nowhere afterwards.
<!-- escalation -->None beyond the answer: behavior-changing finds are named to the user first.
The skill commits nothing.

## Freedom
<!-- latitude -->How the agent finds the mess, which leads it confirms or keeps with a reason, how it
merges duplicates, and the order of the work.

## Gates
<!-- precondition -->A repo.
<!-- postcondition -->The answer block: what is new or came back since last time, removed, merged,
kept and why, found but not changed, and the test counts before and after.
<!-- evidence -->The eval case `evals/cases/cleanup-agent-leftovers`.

## Output
<!-- deliverable -->`plugin/skills/cleanup/SKILL.md` and its eval case.
<!-- acceptance -->`tests/test_spec.py` passes on this brief, and the eval case is judged by outcome
in both arms.
<!-- verification -->`python -m unittest discover tests`
