# Formal check: prove a property for every case, and keep the proof true to the code

## Intent
<!-- purpose -->Every sibling proves things by example: a test, a repro, a check red on one past
commit. Races, retries, state machines and parsers break on the case nobody wrote, so a green suite
says little there. Adapted from pstack's prose `create-formal-verification-skill` and
`maintain-formal-verification-skill` (cursor/plugins, `pstack/skills/`). It began (1.40.0) with a
helper script that scanned for candidates and gated five stages (record, map, run, break, sync);
no eval ever showed the script beating plain Opus, so on 2026-11-09 it became a saved prompt in
plain words (CLAUDE.md, "How a skill is written") and the script and its tests were removed.
<!-- end state -->The user types one word and gets one promise that matters, checked for every
case in a stated scope by a command that passes on the code and fails with the code broken, its
model mapped to lines that exist, kept in the repo so a later change to covered code shows as
stale. `SKILL.md` says the goal, what done looks like, what to avoid and the fixed answer block;
the method is the model's.
<!-- done when -->`SKILL.md` is about one page of plain prose with that answer block, nothing names
the removed script, and the full suite passes.

## Context
<!-- grounding -->
- The dangerous case is a check that keeps passing on a model of code that no longer exists: it
  looks like a proof. Drift is judged from git history since the commit the check was last true
  to, not from memory.
- The verifier (TLA+/TLC, Apalache, Kani, CBMC, Dafny, CrossHair, Hypothesis, an exhaustive
  enumerator) is the target repo's dependency, never ours.
- A failure on the current code is a finding, not a reason to weaken the property; a failure
  after a model update is drift if a step cannot happen in the code, a bug if every step can.
<!-- scope -->The manual-only skill `plugin/skills/formal-check/SKILL.md` and its registration in
CLAUDE.md.
<!-- non-goals -->
- Installing a verifier or calling the network.
- Fixing product code when a property fails: that goes to debug-protocol or the user.
- Blocking verify-loop or safe-release on a stale check.

## Guardrails
<!-- constraints -->
- A check counts only once it was seen failing with one edit to the code, never the model.
- A change to the property, bounds or assumptions is reported with its evidence.
<!-- invariants -->
- Runs and breaks happen in throwaway copies; the product tree is not changed.
<!-- escalation -->Whether a stale check should block other skills is the user's call.

## Freedom
<!-- latitude -->The target, the tool, the model, how it is mapped and kept, and the order of work.

## Gates
<!-- precondition -->A repo with code whose promise tests rarely reach.
<!-- postcondition -->The answer block: outcome, property, harm, target, tool and why, the check
and its break, bounds, assumptions, changes, steps for a bug, and what is not covered.
<!-- evidence -->The answer block itself, judged on a real repo; no paid eval has measured this
skill yet, and `python -m unittest discover tests` covers only this brief.

## Output
<!-- deliverable -->`plugin/skills/formal-check/SKILL.md`.
<!-- acceptance -->`tests/test_spec.py` passes on this brief, and the skill is judged by outcome.
<!-- verification -->`python -m unittest discover tests`
