# Untangle: restructure where the history says changes hurt

## Intent
<!-- purpose -->The user wants a skill that untangles a codebase. The test of success is the next
change, most likely made by an agent: it costs fewer tokens to find what to change, it breaks less
without anyone noticing, and the cause of a bug is found faster. Behavior stays the same. Traces of
plain Opus on a real repo (Transcriber_v2 rewound, three real later fixes replayed as probes) showed
two things. It untangles safely. But it picks tangles it can see in the code (import direction,
copied helpers) and never reads git history, so the files where the next fixes landed were left as
they were.
<!-- end state -->`python plugin/skills/untangle/scripts/untangle.py <repo>` ranks the files that
change and get fixed most, and the pairs that change together. `--gate --run CMD` records the tests
on the committed tree, holds three stages, and prints `UNTANGLE-GATE: done` with an answer that
names real faults first.
<!-- done when -->Every condition under Acceptance passes, the skill is registered like its siblings,
and the full suite passes.

## Context
<!-- grounding -->
- The plugin's rule: mechanics, not advice. caldoai's prose `untangle-codebase` skill was compared
  on the same repo. Both of its runs skipped its own "list every problem first" step and misread
  the red tests, so prose steps are not copied here.
- Results are in `evals/results/2026-11-07-untangle-compare/REPORT.md`. The probes were noise in
  every arm. Ours was the cheapest untangle and the only one to classify the red tests right. It
  skipped the two fix-heavy files where 7 of the 12 later commits landed; the fix-heavy rule
  answers that.
- Tests already red at the start hide real faults: one plain run called the D4 bug a stale test.
<!-- scope -->A new manual-only skill `plugin/skills/untangle/` (SKILL.md and
`scripts/untangle.py`, stdlib only), with state in `.untangle/`. Also `tests/test_untangle.py`,
registration in CLAUDE.md, both plugin manifests and CHANGELOG.md, and the per-session cost fix in
`evals/agent.py` that the comparison found.
<!-- non-goals -->
- Fixing a real fault found along the way: it is marked and named, not fixed, because a fix changes
  behavior.
- An import-graph or layer check: that is latent-audit's and structure-gate's job, and no probe got
  faster from that move.
- Running the replay probes inside the skill: they cost about $0.70 each and belong to an eval case.

## Guardrails
<!-- constraints -->
- One helper, `U`.
  - `U` alone prints the ranking: commits plus twice the fix commits, files untouched in the last
    100 commits left out.
  - `U --gate --run CMD` records the baseline and checks the stages.
- Notes live in `.untangle/notes.md`, in slots the gate drafts:
  - each hotspot and pair is `target` or `skip`;
  - each red test (one slot per file and failure message) is `env`, `stale` or `bug`;
  - each move has a guard.
- A `FIX-HEAVY` hotspot (a third or more of its commits are fixes) is skipped only with a guard the
  gate runs, which names a test file mentioning that module.
- A `bug` names its `file:line`, with a `untangle: known bug:` comment within 3 lines of it.
- A guard must pass on the changed tree and fail in a worktree of the base.
- SKILL.md body is at most 5,000 characters, shaped like its siblings (goal, `U`, stages table).
<!-- invariants -->
- The baseline is taken only on the committed tree, and only when every command ran tests.
  Otherwise nothing is recorded.
- No test green at the baseline goes red, and no command runs fewer tests.
- Guard and suite results are reused only while a hash of the changed tree is the same.
<!-- escalation -->None. The skill reports and untangles; it commits nothing.

## Freedom
<!-- latitude -->How the agent reads the code, what it moves, and which tests it writes as guards.

## Gates
<!-- precondition -->Stage 1, baseline: a git repo with the code committed.
<!-- postcondition -->The tests are recorded, and every hotspot, pair and red test is classified.
<!-- evidence -->`python -m unittest tests/test_untangle.py`
<!-- precondition -->Stage 2, untangle: stage 1 holds.
<!-- postcondition -->Every changed file serves a target, and every move's guard fails on the base.
<!-- evidence -->`python -m unittest tests/test_untangle.py`
<!-- precondition -->Stage 3, same behavior: stages 1 and 2 hold.
<!-- postcondition -->The same suite reruns with nothing green gone red.
<!-- evidence -->`python -m unittest tests/test_untangle.py`

## Output
<!-- deliverable -->`plugin/skills/untangle/` with its helper, plus the release bookkeeping.
<!-- acceptance -->`tests/test_untangle.py` holds every rule above. Each rule, broken in the
helper, turns at least one of its tests red.
<!-- verification -->`python -m unittest discover tests`
