I've created the project's context files under `fixture/` and they pass the helper's structural check. Two parts of the skill were skipped (the search index and the handoff check), and the feature map and test recipe were written by hand rather than with the skills that normally produce them.

**Setup:** plain Python with no packages or manifest, run from `fixture/`. No source or test files changed. Your manual notes are still there: "integer cents", the live gateway note and the existing `agent-routing` block. The `SPEC.md` requirement and the code agree (the code adds 10 cents).

**Commands I ran**
- The helper's `inventory`, then `check` (which ended with no issues after the fixes below), `remember` and `list`.
- `python -m pytest -q` and `python -m unittest discover tests`: 1 test, passes.
- Mutation test: in a throwaway copy, I changed the fee from 10 to 11. The test failed (`FAILED (failures=1)`), so it does catch a wrong fee. It passes again on the real code.

**What I checked and the result:** the fee rule from `SPEC.md`, "`total(100) == 110`". A wrong result fails with "expected total 110". This one behaviour is checked and a deliberate wrong value was caught. I didn't use the `verify-loop` skill's recorder, so there is no strict-green record from it.

| category | file | state | what I did | evidence |
|---|---|---|---|---|
| startup | AGENTS.md | present | refreshed: added one start-here block plus `role: path` pointer lines | the helper's check passes |
| intent | BRIEF.md | present | created from `SPEC.md` and `AGENTS.md`, with unknowns listed | traced from `SPEC.md` |
| work | BUILD.md | present | created, with a `## Next` section | n/a |
| features | FEATURES.md | present | created by hand; the `feature-map` skill wasn't run | proven: unittest pass plus the mutation test |
| verify | VERIFY.md | present | refreshed: added the selected behaviour, command, failure message and challenge; kept your MANUAL blind spot | proven: unittest and mutation test |
| architecture | docs/architecture.md | present | created | traced: `app.total` to `tests/test_total.py` |
| commands | docs/commands.md | present | created | proven: the unittest command |
| memory | .project-context/index.sqlite | **missing** | not built | gap: the project-context index was skipped |

I also added `verification/mutation.md`, which describes the fee mutation test.

**To get the helper's check passing I had to:**
- Change `BUILD.md`'s "Next:" line to a `## Next` heading.
- Add one-line pointers (`intent: BRIEF.md` and so on) to the start-here block.

**Not done:**
- **Memory:** there's no search index, and the "ignore `.project-context/`" step wasn't needed because no index exists yet.
- **Handoff check:** I skipped the recall skill's `context_budget.py --check-handoff`.
- **Up-to-date check:** the helper still says freshness is unknown because there was no earlier snapshot; the snapshot I saved will let a later run tell what changed.
- **Untested behaviour:** `SPEC.md` doesn't say what should happen with negative, zero or non-whole-number amounts, so nothing checks them. The live payment gateway is outside this project.

**Next step:** decide how `total` should handle negative or non-whole-number cents, then add a check for it. After that, build the memory index and run the handoff check.

<!-- file written by the agent: fixture/BRIEF.md -->
# Brief

Goal: a Python checkout library whose `total(cents)` adds a fixed 10-cent fee (source: SPEC.md).

## Decisions in force
- Amounts are integer cents (AGENTS.md, manual).
- No CI or deployment setup requested (AGENTS.md).
- The live payment gateway is outside this project (VERIFY.md, manual).

## Unknowns
- Behavior for negative, zero or non-integer input is not specified.


<!-- file written by the agent: fixture/BUILD.md -->
# Build

State: one function `total` in app.py, one passing unit test.
## Next
get an owner decision on invalid input (negative / non-integer cents), then add a check for it.


<!-- file written by the agent: fixture/FEATURES.md -->
# Features

| Feature | Requirement | Entry point | Implementation | Check | Evidence |
|---|---|---|---|---|---|
| Checkout total adds 10-cent fee | SPEC.md "Checkout" | `app.total(cents)` | app.py:1 | tests/test_total.py::TotalTest.test_fee | proven (unittest pass; fee mutation rejected) |

Unmapped: none known. Written by hand (feature-map not run).


<!-- file written by the agent: fixture/docs/architecture.md -->
# Architecture (as-is)

- `app.py`: `total(cents) -> int`, adds fixed 10-cent fee. No imports, no I/O.
- `tests/test_total.py`: unittest importing `app.total`.
- External: live payment gateway, not in this project (no code references it).
- Unknowns: no packaging/manifest; callers outside this folder unknown.


<!-- file written by the agent: fixture/docs/commands.md -->
# Commands

| Purpose | Command | Working dir | Prereq | Status |
|---|---|---|---|---|
| Unit tests | `python -m unittest discover tests` | `fixture/` | Python 3 | observed pass 2026-10-13 |

No build, lint, CI or deploy commands exist.


<!-- file written by the agent: fixture/verification/mutation.md -->
# Mutation challenge

Mutation: in a disposable copy, change `cents + 10` to `cents + 11` in app.py.
Expected: `python -m unittest discover tests` fails with "expected total 110".
Observed 2026-10-13: failed as expected (rejected); original passes.
