---
name: state-machines
description: >-
  Find the state machines a codebase never declared (status strings, flag combinations, fields whose None means "not yet"), draw each one, and prove each bug in them with a test that fails on the code as it was. Use for "find the implicit state machines", "what states can an order be in", "which states are impossible or stuck".
disable-model-invocation: true
metadata:
  stage: review
  card: "find the state machines nobody declared"
---

# State machines

**Goal:** the user sees every implicit state machine as a picture, knows in plain words which ones
have bugs, and each bug is held by a test that fails on the code as it was. The bugs live in the gaps:
a value checked but never set, a flag combination that should be impossible but is reachable, a state
nothing leaves, a move that skips its guard. Fix only what the user asked you to fix.
`S` is `python <this skill's base directory>/scripts/states.py <repo>`, run from the repo root.

1. `S [paths] --run "<test cmd>"` before you change anything. It lists candidate fields in
   `.states/candidates.md` with every write and every check by `file:line`, records the tests, and
   copies the tree as it was to `.states/before/`. Values marked **checked but never set** are a
   typo, a renamed state, or data from outside; each needs a finding either way.
2. Read the code and write `.states/machines.json`:
   `machines`: `name`, `fields` (candidate ids or field names), `initial`, `states`, `terminal`,
   `transitions` (`from` or `"*"`, `to`, `at` as `path:line` or `path:function`), and `also`
   (`at`, `why`) for writes that are not moves, such as loading saved data.
   `dismissed`: `candidate`, `why`, for leads that are not machines (independent preferences are
   not a machine: every combination is legal).
   `findings`: `kind` (`bug` or `ok`), `machine`, `what`, `at`, `covers` (ids such as
   `value:status=canceled` or `deadend:<machine>:<state>`), and for a bug `test` and `fixed`;
   for `ok`, `why`.
   Look for guards outside the function too (decorators, callers) before you call a move unguarded.
3. Prove each bug with a test command. A fixed bug's test goes in the suite. An open bug's test goes in
   `.states/proofs/` (run it with e.g. `python -m unittest discover -s .states/proofs`) so the suite
   stays green.
4. `S --done`. It refuses while a candidate is unmapped and undismissed, a write it saw is no
   transition, a written value is no state, a checked-never-set value or a state nothing leaves has
   no finding, a bug's test passes on the tree as it was or fails there on an import error, a fixed
   bug's test fails now, or a test that passed now fails. Fix the cause, never the check. It writes
   `.states/MACHINES.md` (a diagram per machine) and prints `STATES: done`.

The answer, in plain words: each machine and its states; bugs, fixed or open, each with the test
that proves it; what looked like a bug and is not (and why). Point the user at `.states/MACHINES.md`
for the pictures.
