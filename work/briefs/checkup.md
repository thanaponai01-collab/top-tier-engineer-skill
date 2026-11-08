# Checkup: one report on how well a codebase is structured, ranked by where changes land

## Intent
<!-- purpose -->The user wants one thing to run on any codebase that says how well structured it
is, and what to fix first. Today that takes five skills (structure-gate, untangle, latent-audit,
arch-design's dep-map, feature-map), and the user has to know which one to run and
then combine their outputs by hand. The test of success: the report puts first the problems that
cost the next change, not the ones that just look worst. A tangled function nobody ever changes
costs less than two files that always change together with nothing linking them.
<!-- end state -->`python plugin/skills/checkup/scripts/checkup.py <repo>` runs the existing
helpers over the repo's git-tracked files and prints one report with one section per property:
easy to find things, one change in one place, dependencies point one way, deep modules, one way
per job, logic apart from I/O, dead code, and tests that can fail. Each section is measured or
says `not checked: <why>`. `--gate` holds four stages and prints `CHECKUP-GATE: done` with an
answer: a verdict per property and the top three things to fix, each one tied to the history.
<!-- done when -->Every condition under Acceptance passes, the skill is registered like its
siblings, the full suite passes, and the eval case below has been run on both arms.

## Context
<!-- grounding -->
- The plugin's rule: mechanics, not advice. The skill is a goal plus gates the helper checks
  (latent-audit 1.28.0 is the template), not a list of how-to steps.
- Every property from the conversation already has a helper that measures it, except "tests that
  can fail" (verify-loop needs a test run) and "one way per job". dep-map.py's I/O section lists
  which modules import which network, database or process library, so two libraries doing one job
  (`requests` in one module, `urllib.request` in another) can be counted from data that already
  exists.
- Run on this repo on 2026-11-07: structure.py took 1.4s and untangle.py 0.3s. graph-audit.py
  took 80s, and both it and wire.py walked `.claude/worktrees/`, which is excluded from git:
  1,696 modules and 1,438 files, against 5,760 tracked files. Most of the dead-module and
  way-in lines came from worktree copies. A checkup that reports those is noise. structure.py
  (through structure-report.py) walked them too, run on the repo root.
- arch-design's change-map.py reports only pairs in different folders (first two path parts),
  so two files side by side that always change together are invisible to it. checkup counts
  pairs from its own read of the history instead.
- Past evals: plain Opus asked to "review the structure" has often matched these skills. What it
  missed, in the untangle comparison, was the history: it fixed tangles it could see and skipped
  the files where the next 7 of 12 fixes landed. That ranking is the gain this skill has to show.
<!-- scope -->A new manual-only skill `plugin/skills/checkup/` (SKILL.md and
`scripts/checkup.py`, stdlib only) that calls the sibling helpers by path when they are
installed. State goes in `.checkup/`. Also: `tests/test_checkup.py`; making graph-audit.py,
wire.py and structure-report.py skip git-ignored paths and `.checkup/`; one eval case `evals/cases/checkup-ugly-but-idle/`; registration
in CLAUDE.md, both plugin manifests and CHANGELOG.md, as 1.43.0.
<!-- non-goals -->
- Fixing anything in the checked codebase. The report names the skill that fixes each finding
  (untangle, latent-audit, arch-design) when it is installed.
- Running the checked project's tests. "Tests that can fail" is always `not checked` here and
  names verify-loop, which runs the tests against broken code.
- New measurements inside the sibling helpers, beyond skipping ignored paths. If a property needs
  a new measurement, it goes in that sibling.
- Languages other than Python beyond what structure.py already measures (length and copies). The
  report says which sections are Python only.

## Guardrails
<!-- constraints -->
- One helper, `C`.
  - `C <repo>` prints the report.
  - `C <repo> --gate` checks the stages and drafts the slots in `.checkup/notes.md`.
- The report opens with what was measured: files and lines counted, the share each helper
  entered, and each helper that was missing or failed, before any finding.
- Only git-tracked files count. A finding in an ignored or untracked path is dropped and counted.
- Each finding gets a weight from the history, counted the way untangle.py counts: commits plus
  twice the fix commits of its files in the last 300 (for a pair, only the commits that touched
  both). Findings are listed by weight, highest first. A finding no commit in the last 100
  touched is labeled `idle`.
- A pair is two tracked files that changed together in 3 or more commits; a pair with a test file
  in it is left out, since a test changes with its code by design.
- "One way per job" groups dep-map's I/O libraries by job (http, database, process, mail). A job
  done by two or more libraries is a finding that names each module.
- A section that no helper measured says `not checked: <why>`, never "clean" or "fine".
- SKILL.md body is at most 5,000 characters, shaped like its siblings (goal, `C`, stages table).
<!-- invariants -->
- The checked repo is never written, except `.checkup/`.
- A sibling helper's own verdict is quoted, never reworded into a stronger one.
- Reruns are cheap: helper output is cached in `.checkup/` and reused only while the hash of the
  tracked files is the same.
<!-- escalation -->None. The skill only reports. Fixing goes to the named sibling skill, on the
user's say.

## Freedom
<!-- latitude -->How the agent reads the code behind a finding, which findings it digs into past
the top three, and how it words the cost of each.

## Gates
<!-- precondition -->Stage 1, measure: a git repo with at least one tracked code file.
<!-- postcondition -->Every section is either measured or `not checked: <why>`. Every helper that
was missing or failed is named, and the measured share comes before the first finding.
<!-- evidence -->`python -m unittest tests/test_checkup.py`
<!-- precondition -->Stage 2, account: stage 1 holds.
<!-- postcondition -->Going down by weight until three are not `none:` (at most twelve), plus
any finding the agent adds, each has `cost: <the commits that show what it costs>` or `none: <why the shape is
right>` in `.checkup/notes.md`. A note naming a finding the report does not hold fails.
<!-- evidence -->`python -m unittest tests/test_checkup.py`
<!-- precondition -->Stage 3, read: stages 1 and 2 hold.
<!-- postcondition -->Each of the eight non-test code files changes land in most has
`risk: <name>(): <what can go wrong>` or `nothing: <name>(): <what it does>`, and `<name>` appears in
that file. Every `risk:` is printed in the answer before the fixes, so a bug no section measures
is not lost behind the structure findings.
<!-- evidence -->`python -m unittest tests/test_checkup.py`
<!-- precondition -->Stage 4, answer: stages 1 to 3 hold.
<!-- postcondition -->Each property has `good | in places | poor | not checked`. `good` fails
while its section is not measured, or while it has a finding with a cost. The top three to fix
are findings with a cost, highest weight first. An `idle` finding goes in the top three only with
a `cost:` note that names the coming change it will slow down.
<!-- evidence -->`python -m unittest tests/test_checkup.py`

## Output
<!-- deliverable -->`plugin/skills/checkup/` with its helper, the ignored-path fix in
graph-audit.py, wire.py and structure-report.py, the eval case and its results under
`evals/results/<date>-checkup/`, and the release bookkeeping.
<!-- acceptance -->`tests/test_checkup.py` holds every rule above, and each rule, broken in the
helper, turns at least one of its tests red. `tests/test_graph_audit.py` (and wire.py's
tests, removed with wire.py when wire-check went to prose) gain a case where a git-ignored folder
holds a copy of a module and is not reported. The eval
case has a fixture whose ugliest file is never changed, while the real cost is two files that
change together with no import between them, and a second HTTP library. The skill arm puts the
pair first in 3 of 3 runs. The plain-Opus arm's result is reported as found, whether it ties or
not.
<!-- verification -->`python -m unittest discover tests`
