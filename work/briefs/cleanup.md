# Cleanup: clear what agents leave behind

## Intent
<!-- purpose -->The user wants a skill that leaves a codebase the next agent can work in without
being misled. Agents leave things behind: dead code, orphaned files, `_v2`/`_old` copies,
duplicated helpers, two ways of doing one job, debug prints, commented-out code, silent failures,
stubs, and comments about past changes. The user rarely spots these, but they all come up when
the user asks an agent to find what is redundant. So a plain agent already finds part of this when
asked. The skill earns its place only if, on the same request, it finds more of it, breaks less
(the real danger is deleting something that looked unused but was loaded by name), and puts first
the smells that mislead most: parallel implementations, silent failures and code written to pass a
test. It cleans the mess. It does not reshape the building.
<!-- end state -->The user types one word and gets a cleanup without explaining it again. Plain
Opus already cleans a small repo perfectly when asked in full (evals/results/2026-11-07-cleanup-plain:
3/3, 12/12 mess removed, every decoy kept), and the user is fine with that: the skill exists so the
request does not have to be explained every time, at close to plain cost. `python
plugin/skills/cleanup/scripts/cleanup.py <repo> [paths]` lists candidate mess, `--run CMD` records
the tests before any change, and `--done --run CMD` refuses done while tests got worse or a deleted
file is still named somewhere, then saves the record the next run compares against and prints
`CLEANUP: done`.
<!-- done when -->Every condition under Acceptance passes, the eval case passes with the skill as it
does without, the skill is registered like its siblings, and the full suite passes.

## Context
<!-- grounding -->
- The user does not read code. The answer must be plain words first, `file:line` second.
- The user cannot look after hooks, linters or CI rules. Protection that needs upkeep turns into
  slow checks, false alarms and bypasses, so none is installed. A record of each run replaces it.
- The user wants to invoke it without explaining; it is fine that plain Opus already passes.
- Past ports show plain Opus often ties. Gains came where a script caught what the agent skipped,
  so every rule here is a check the helper runs, not a step to follow.
- Fixing a silent failure, a stub or code that games a test changes what the program does. In 2 of
  3 plain runs Opus fixed the test-gaming bug and said so plainly; that is allowed when the answer
  names the change in behavior.
<!-- scope -->A new manual-only skill `plugin/skills/cleanup/` (SKILL.md and `scripts/cleanup.py`,
stdlib only), with state in `.cleanup/`. Also `tests/test_cleanup.py`, the eval case, and
registration in CLAUDE.md, both plugin manifests and CHANGELOG.md.
<!-- non-goals -->
- Hooks, linter configs, pre-commit or CI rules: the user cannot maintain them.
- Restructuring (splitting big files, moving modules, layers): that is untangle's and arch-design's
  job. A god file found here is pointed at untangle, not split.
- Measuring complexity: structure-gate's job.
- Checks against one repeated mistake: mistake-proof's job.

## Guardrails
<!-- constraints -->
- One helper, `C`, lean on purpose: no per-candidate notes, no stage gate.
  - `C <repo> [paths]` lists candidates in `.cleanup/candidates.md` by `file:line` and kind:
    leftover-version names, litter, orphaned modules, dead functions, duplicate functions, unused
    imports, debug leftovers, commented-out code, swallowed errors, stubs, hard-coded answers and
    change-log comments. Python is read by AST; other files by name and text only. With a record
    from an earlier run it also lists what is new since then and what came back after deletion.
  - `C --run CMD` records the file list and the test result before any change.
  - `C --done --run CMD` reruns the tests and refuses done when they fail where they passed, ran
    fewer, or a deleted file's name is still in a text file. Otherwise it saves the record to
    `.cleanup/history.json` and prints `CLEANUP: done`.
- Swallowed errors, stubs and hard-coded answers change behavior when fixed. The skill says so; a
  fix is allowed only when the answer names it as a change in behavior.
- SKILL.md body is at most 3,000 characters.
<!-- invariants -->
- No test that passed before fails after, and the command never runs fewer tests.
- The record is written only by `--done` once it holds.
<!-- escalation -->None beyond the answer: behavior-changing finds are named to the user first.
The skill commits nothing.

## Freedom
<!-- latitude -->How the agent reads the code, which candidates it confirms or dismisses with a
reason, how it merges duplicates, and the order of the work.

## Gates
<!-- precondition -->Stage 1, find: a repo.
<!-- postcondition -->Candidates are listed and the tests are recorded before any change.
<!-- evidence -->`python -m unittest tests/test_cleanup.py`
<!-- precondition -->Stage 2, done: the recorded tests exist.
<!-- postcondition -->Nothing that passed fails, no fewer tests ran, no deleted file is still named,
and the record is saved; a later find shows what came back.
<!-- evidence -->`python -m unittest tests/test_cleanup.py`

## Output
<!-- deliverable -->`plugin/skills/cleanup/` with its helper, the eval case and its report, plus the
release bookkeeping.
<!-- acceptance -->`tests/test_cleanup.py` holds every rule above. Each rule, broken in the helper,
turns at least one of its tests red. The eval case passes with the skill.
<!-- verification -->`python -m unittest discover tests`
