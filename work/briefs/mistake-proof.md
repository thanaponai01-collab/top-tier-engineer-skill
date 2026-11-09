# Mistake proof: make a repeated agent mistake impossible

## Intent
<!-- purpose -->Agents in a repo keep making the same mistakes, and the usual fix is a new line in
CLAUDE.md that the next agent never reads, so nothing fails when it is skipped. Adapted from
pstack's prose `correct` skill (cursor/plugins, `pstack/skills/correct/SKILL.md`). It began (1.39.0)
with a helper script that mined candidates, gated four stages (classes, level, proof, rule table)
and checked the reply; no eval ever showed the script beating plain Opus, so on 2026-11-09 it
became a saved prompt in plain words (CLAUDE.md, "How a skill is written") and the script and its
tests were removed.
<!-- end state -->The user types one word and gets each repeated mistake as a class with two real
pieces of evidence, fixed at the strongest level that works with a reason each stronger level did
not, held by a check that fails on the commit with the mistake and passes now, and named as a rule
with its enforcer in the agent file. `SKILL.md` says the goal, what done looks like, what to avoid
and the fixed answer block; the method is the model's.
<!-- done when -->`SKILL.md` is about one page of plain prose with that answer block, nothing names
the removed script, and the full suite passes.

## Context
<!-- grounding -->
- Where mistakes show up without a chat log: reverts, commits that bring a reverted change back,
  fix commits that name an earlier one, and workaround comments (`# don't`, `# must`, `NOTE:`)
  next to code. The operator's correction in this session is evidence too.
- A class counts once it has happened twice; one occurrence is a bug for debug-protocol.
- Fix levels, strongest first: 1 architecture, 2 types, 3 a lint or CI check naming the right
  file, type or function, 4 a test, 5 docs only for judgment calls. A lower level needs a reason
  why each stronger one did not work. Deleting an old way with live callers goes to evolve-maintain.
- Agents copy the nearest example. If the bad pattern is already common, a check that fails on
  every old use will be switched off; it fails only on what a change adds.
<!-- scope -->The manual-only skill `plugin/skills/mistake-proof/SKILL.md` and its registration in
CLAUDE.md and both plugin manifests.
<!-- non-goals -->
- Reading other sessions' transcripts or calling GitHub for review comments.
- Planning a large migration when a level-1 fix deletes something with live callers.

## Guardrails
<!-- constraints -->
- A class at levels 1-4 is fixed only by a check that was run failing on the past mistake and
  passing on the working tree; a level-5 class is reported `unenforced`.
- Each rule in the agent file names its enforcer, or `none` at level 5; a level-5 rule broken
  again is a repeat and gets fixed at level 1-4.
<!-- invariants -->
- Proofs on past commits run in throwaway copies; the product tree changes only by the fixes.
<!-- escalation -->An exception needs a human's name as approver; the agent never fills it.

## Freedom
<!-- latitude -->How candidates are mined and grouped, how a check is applied to a past commit, and
the order of work.

## Gates
<!-- precondition -->A git repo with history, or a correction from the operator.
<!-- postcondition -->The answer block: classes, each with evidence, level, why not stronger, check
and enforcer, then repeats and what was not checked.
<!-- evidence -->The answer block itself, judged on a real repo; no paid eval has measured this
skill yet, and `python -m unittest discover tests` covers only this brief.

## Output
<!-- deliverable -->`plugin/skills/mistake-proof/SKILL.md`.
<!-- acceptance -->`tests/test_spec.py` passes on this brief, and the skill is judged by outcome.
<!-- verification -->`python -m unittest discover tests`
