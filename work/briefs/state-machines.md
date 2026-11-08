# State machines: find the ones the code never declared

## Intent
<!-- purpose -->The user asked for a skill behind the prompt "find all of the implicit state machines
in my app". Most apps hold state machines nobody wrote down: a status string set in six files and
checked in twelve, booleans that only make sense in some combinations (`printing` and `error` both
true), a field whose `None` means "not yet". The bugs live in the gaps: a value that is checked but
never set (a typo, or a renamed state), a combination of flags that should be impossible but is
reachable, a state with no way out, a transition that skips its guard. A plain agent given the
prompt finds some machines and describes them. The skill earns its place only if it finds more of
the write sites, catches the checked-but-never-set values a reader skims past, and proves each bug
it reports with a test that fails on the code as it was.
<!-- end state -->The user types one word and gets every implicit state machine drawn as a picture
with its states and transitions, the bugs in plain words, each bug held by a test that failed on the
code as it was, and the bugs they asked to fix fixed without breaking anything. `python
plugin/skills/state-machines/scripts/states.py <repo>` lists candidate state fields with every
write and every check by `file:line`; `--run CMD` records the tests and the tree before any change;
`--done` refuses while the map misses a write the helper saw, a checked-but-never-set value or a
state with no exit is neither a finding nor explained, a bug's test does not fail on the tree as it
was, or a test that passed now fails; then it writes `.states/MACHINES.md` and prints
`STATES: done`.
<!-- done when -->Every condition under Acceptance passes, the eval case is run with and without
the skill and its result reported honestly, the skill is registered like its siblings, and the full
suite passes.

## Context
<!-- grounding -->
- The user does not read code. Each machine is shown as a diagram, bugs in plain words first,
  `file:line` second.
- Past ports show plain Opus often ties on finding. Gains came where a script caught what the
  agent skipped (feature-map alarm, debug-protocol distant cause), so every rule here is a check
  the helper runs, not a step to follow.
- A string value compared in one file but written nowhere is the cheapest bug to catch by script
  and the easiest to skim past by eye; it gets its own rule.
- Two booleans set together are not always a machine: independent preferences (email on, SMS on)
  allow every combination. A cluster is a lead, never a verdict.
<!-- scope -->A new manual-only skill `plugin/skills/state-machines/` (SKILL.md and
`scripts/states.py`, stdlib only), with state in `.states/`. Python is read by AST; JS and TS by
text patterns for `x.status = "..."` and `=== "..."`. Also `tests/test_states.py`, the eval case,
and registration in CLAUDE.md, both plugin manifests and CHANGELOG.md.
<!-- non-goals -->
- Rewriting the app around a state-machine library or an enum: the user can ask for that later.
- Proving a machine correct in general: formal-check's job.
- Hooks, linters or CI rules: the user cannot maintain them.

## Guardrails
<!-- constraints -->
- One helper, `S`, three commands.
  - `S <repo> [paths]` writes `.states/candidates.md`: each field assigned string literals or
    booleans in two or more places, with every write and check by `file:line`; values checked but
    never written; values written but never checked; flag groups set on one object.
  - `S --run CMD` records the test result and a copy of the tracked source before any change.
  - `S --done` reads `.states/machines.json` (machines with fields, states, transitions with
    `at`, terminal states, findings, dismissed candidates) and refuses when: a candidate is in no
    machine and not dismissed with a reason; a write the helper saw for a mapped field is in no
    transition; a written value is not a state; a checked-but-never-set value or a non-terminal
    state with no exit is not covered by a finding; a finding of kind bug has no test command, or
    its test passes on the copy of the tree as it was; a test that passed now fails or fewer run.
    Otherwise it writes `.states/MACHINES.md` (a mermaid diagram per machine, findings with fixed
    or open) and prints `STATES: done`.
- SKILL.md body is at most 3,000 characters.
<!-- invariants -->
- No test that passed before fails after, and the command never runs fewer tests.
- The tree as it was is copied before any change and never edited.
<!-- escalation -->Bugs the user did not ask to fix are reported, not fixed. The skill commits
nothing.

## Freedom
<!-- latitude -->How the agent reads the code, which candidates it groups into one machine, which it
dismisses, how it writes each test and each fix, and the order of the work.

## Gates
<!-- precondition -->Stage 1, find: a repo.
<!-- postcondition -->Candidates are listed with every write and check, and the tests and the tree
are recorded before any change.
<!-- evidence -->`python -m unittest tests/test_states.py`
<!-- precondition -->Stage 2, map and prove: candidates and the recorded tree exist.
<!-- postcondition -->Every candidate is mapped or dismissed, every write is a transition, every
suspicious value and dead end is a finding, and every bug's test fails on the tree as it was.
<!-- evidence -->`.states/machines.json` and `python -m unittest tests/test_states.py`
<!-- precondition -->Stage 3, done: the map passes.
<!-- postcondition -->No test that passed fails, `.states/MACHINES.md` is written with each finding
fixed or open.
<!-- evidence -->`python -m unittest tests/test_states.py`

## Output
<!-- deliverable -->`plugin/skills/state-machines/` with its helper, the eval case and its result,
plus the release bookkeeping.
<!-- acceptance -->`tests/test_states.py` holds every rule above. Each rule, broken in the helper,
turns at least one of its tests red. The eval case is run in both arms.
<!-- verification -->`python -m unittest discover tests`
