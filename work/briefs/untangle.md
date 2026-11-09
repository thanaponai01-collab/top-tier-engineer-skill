# Untangle: restructure where the history says changes hurt

## Intent
<!-- purpose -->The user wants a skill that untangles a codebase. The test of success is the next
change, most likely made by an agent: it costs fewer tokens to find what to change, it breaks less
without anyone noticing, and the cause of a bug is found faster. Behavior stays the same. Traces of
plain Opus on a real repo (Transcriber_v2 rewound, three real later fixes replayed as probes) showed
that it untangles safely but picks tangles it can see in the code (import direction, copied
helpers) and never reads git history, so the files where the next fixes landed were left as they
were. It began (1.41.0) with a helper script that ranked hotspots from history and gated three
stages; 84 Sonnet replay runs tied every arm, plain Opus included
(evals/results/2026-11-07-untangle-sonnet-probes), so on 2026-11-09 it became a saved prompt in
plain words (CLAUDE.md, "How a skill is written") and the script and its tests were removed.
<!-- end state -->The user types one word and gets an untangle without explaining it again: targets
picked from the history, red tests sorted before any change, real faults marked and named, and the
same tests passing after. `SKILL.md` says the goal, what done looks like, what to avoid and the
fixed answer block; the method is the model's.
<!-- done when -->`SKILL.md` is about one page of plain prose with that answer block, nothing names
the removed script, and the full suite passes.

## Context
<!-- grounding -->
- Results are in `evals/results/2026-11-07-untangle-compare/REPORT.md` and
  `evals/results/2026-11-07-untangle-sonnet-probes/REPORT.md`. The probes were noise in every arm.
  The script arm skipped the two fix-heavy files where 7 of the 12 later commits landed; the prose
  keeps the rule that a fix-heavy file is skipped only when a test catches its fixes being undone.
- Tests already red at the start hide real faults: one plain run called the D4 bug a stale test.
<!-- scope -->The manual-only skill `plugin/skills/untangle/SKILL.md` and its registration in
CLAUDE.md and both plugin manifests.
<!-- non-goals -->
- Fixing a real fault found along the way: it is marked and named, not fixed, because a fix changes
  behavior.
- An import-graph or layer check: that is latent-audit's and structure-gate's job.
- Dead code and litter: cleanup's job.
- Running the replay probes inside the skill: they cost about $0.70 each and belong to an eval.

## Guardrails
<!-- constraints -->
- Targets come from the history: files with many commits and fix commits, and pairs that change
  together. Each gets a target or a reason to skip.
- Every changed file serves a target; past fixes are not undone.
<!-- invariants -->
- The tests are run on the committed tree before any change; red ones are sorted env, stale or bug.
- No test green before goes red, and no fewer tests run.
<!-- escalation -->None beyond the answer: known bugs are named first. The skill commits nothing.

## Freedom
<!-- latitude -->How the agent reads the code and the history, what it moves, and which tests it
writes as guards.

## Gates
<!-- precondition -->A git repo with the code committed.
<!-- postcondition -->The answer block: known bugs, targets, skips, red tests sorted, guards, and the
test counts before and after.
<!-- evidence -->The replay probes in `evals/results/2026-11-07-untangle-sonnet-probes`.

## Output
<!-- deliverable -->`plugin/skills/untangle/SKILL.md`.
<!-- acceptance -->`tests/test_spec.py` passes on this brief, and the untangle is judged by outcome.
<!-- verification -->`python -m unittest discover tests`
