# Blast radius: what a change breaks outside its diff

## Intent
<!-- purpose -->A change can be proven to do what it meant (verify-loop) and be wired in (wire-check)
and still break code it never touched: a caller that passes the old arguments, a reader of a JSON
key or column it renamed, a script that reads an env var it dropped. Adapted from pstack's prose
`blast-radius` skill (cursor/plugins, `pstack/skills/blast-radius/SKILL.md`). It began (1.38.0) with
a helper script that listed consumers, gated three stages and recorded the 1-to-5 sureness level;
no eval ever showed the script beating plain Opus, so on 2026-11-09 it became a saved prompt in
plain words (CLAUDE.md, "How a skill is written") and the script and its tests were removed.
<!-- end state -->The user types one word and gets every consumer of what the diff changed, outside
the diff, each with a cited `breaks`, `cleared` or `unknown`, and `safe` only when the one fact the
change is safe because of has a proof that passes on the change and fails with that fact broken.
`SKILL.md` says the goal, what done looks like, what to avoid and the fixed answer block; the
method is the model's.
<!-- done when -->`SKILL.md` is about one page of plain prose with that answer block, nothing names
the removed script, and the full suite passes.

## Context
<!-- grounding -->
- Breakage a symbol search misses is the point: string uses of a changed name (dict keys, JSON
  fields, column names, env vars, flag names, CLI options) in any text file, and callers several
  imports away.
- Most risky-looking changes are safe because of one fact ("this call only drops cache entries
  that are already dead"). Proving that one fact clears most risks at once; a list of maybes does
  not.
- Sureness ladder: 1 said so, 2 cited `file:line`, 3 walked the failure, 4 ran it (a command that
  fails when the fact is false), 5 reproduced in the running app.
<!-- scope -->The manual-only skill `plugin/skills/blast-radius/SKILL.md` and its registration in
CLAUDE.md and both plugin manifests.
<!-- non-goals -->
- Fixing what it finds: report only.
- Running several models on the same question (pstack's `arena` step).
- Searching consumers outside the repo: they get `unknown`, naming what they depend on.

## Guardrails
<!-- constraints -->
- Every consumer outside the diff gets `breaks`, `cleared` or `unknown`; the first two cite the
  `file:line` or library source they rest on.
- `safe` needs no consumer that breaks and a proof run failing with the fact broken and passing on
  the change; below level 4 the answer says `unproven`.
<!-- invariants -->
- The product tree is never written: proofs and breaks run on throwaway copies.
<!-- escalation -->Whether a `breaks` finding should block `safe-release` is the user's call; this
skill only reports.

## Freedom
<!-- latitude -->How consumers are found and ranked, how the break is made, and the order of work.

## Gates
<!-- precondition -->A git repo and a change against a base ref.
<!-- postcondition -->The answer block: verdict, what changed, every consumer's verdict, the fact,
its proof and the level.
<!-- evidence -->The answer block itself, judged on a real change; no paid eval has measured
this skill yet, and `python -m unittest discover tests` covers only this brief.

## Output
<!-- deliverable -->`plugin/skills/blast-radius/SKILL.md`.
<!-- acceptance -->`tests/test_spec.py` passes on this brief, and the skill is judged by outcome.
<!-- verification -->`python -m unittest discover tests`
