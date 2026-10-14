All eight context categories now exist and pass their checks. The one requirement-backed behavior, the checkout fee, is **verified locally: strict green, and a deliberately wrong version of the code was rejected**. I didn't change any product code or manual notes.

## Context files

| Category | File | State | What I did | Evidence |
|---|---|---|---|---|
| startup | `AGENTS.md` | present | **refreshed**: added one start-here block (19 lines) below your existing text, which is unchanged | *proven*: the foundation `check` and handoff check found 0 issues |
| intent | `BRIEF.md` | present | **created** from SPEC.md and AGENTS.md; open questions are listed explicitly | *traced*: every line cites its source |
| work | `BUILD.md` | present | **created**: current result, blockers, one Next step with its done check | *proven*: handoff check found 0 structural gaps |
| features | `FEATURES.md` | present | **created**: the feature-map scan found 0 entry points because this is a library, so I mapped `total(cents)` by hand | *proven*: `features.py check --strict` passes with every count at 0 |
| verify | `VERIFY.md` | present | **refreshed**: added the "Checkout fee" check; your `MANUAL:` gateway line is kept word for word; added 2 blind spots | *proven*: strict run passes and `status` says `VERIFY-STATE: green` |
| architecture | `docs/architecture.md` | present | **created**: a small as-is map with cited lines and the unknowns | *traced*: from the test import to `app.py:1-2` |
| commands | `docs/commands.md` | present | **created** | *proven*: each listed command was run and its result recorded |
| memory | `.project-context/index.sqlite` | present | **created**: indexed once, then re-indexed only `AGENTS.md` after it changed | *proven*: `context.py check` reports no issues, and a search returns the docs |

I also added `verification/fee-mutation.json` (the deliberate mistake used for the test). The run left `.verify-state.json`, `.project-context/foundation.json` and `__pycache__/`.

## Verification
- **Runtime:** Python 3.13.4, standard library only. All commands run from `fixture/`.
- **Claim tested:** SPEC.md says `total(100)` returns `110` (a fixed 10-cent fee).
- **Rejection shown:** a copy of the code with `cents + 10` changed to `cents + 1` failed with `AssertionError: 101 != 110 : expected total 110`. The original passed.
- **Commands I ran:** `unittest discover tests`, `features.py init` and `check --strict`, `verify.py` (`challenge`, `baseline`, `run --strict`, `status`, `tests --strict`), `context.py index` and `check`, `foundation.py inventory`, `check`, `remember` and `list`, and `context_budget.py --check-handoff`.
- **Unchanged:** I confirmed that `app.py`, `SPEC.md` and the test still match the originals.
- One `status` came back `stale`, because I wrote the docs after the first strict run. I re-ran strict on the final files and it is green.

## Gaps
- **Untested:** only the input 100 is checked. SPEC.md doesn't say what should happen with zero, negative or non-integer amounts. These are recorded as owner questions, not filled in with guesses.
- **Out of scope:** the live payment gateway, which is not part of this folder.
- **No git repository**, so:
  - FEATURES.md can't pin its status to a commit, which means it won't automatically flag drift.
  - There was no existing ignore file to follow, so I didn't create a `.gitignore`. If you run `git init`, add `.verify-state.json`, `.project-context/` and `__pycache__/` to it.
- **No helper agents:** the routing block names `drive-executor` and `setup-reader`, but those agents aren't available in this session. I did everything myself, which the setup instructions allow.

**Next step:** have the owner define how edge-case inputs should behave (see BRIEF.md). Then add a test for each and get the strict run green again.

<!-- file written by the agent: fixture/BRIEF.md -->
# Brief

## Goal
A Python checkout library whose total is the supplied price plus a fixed 10-cent fee.
Source: SPEC.md.

## Constraints (in force)
- Amounts are integer cents. Source: AGENTS.md (MANUAL).
- Preserve product behavior and the live gateway note. Source: AGENTS.md.
- No CI or deployment setup. Source: AGENTS.md.

## Acceptance
- `total(100)` returns `110` (fee of 10 cents). Source: SPEC.md; checked by VERIFY.md "Checkout fee".

## Decisions
- None recorded beyond the constraints above. A changed decision replaces its line here.

## Open questions (owner)
- Behavior for zero, negative or non-integer input is unspecified (SPEC.md is silent).
- How the live payment gateway relates to this library is unknown; it is out of this project.


<!-- file written by the agent: fixture/BUILD.md -->
# Build

## Current result
- Context foundation prepared 2026-10-11. Product code unchanged.
- "Checkout fee" verified: strict run green; mutation `+ 10` → `+ 1` rejected with "expected total 110".

## Blockers
- None for current scope. Edge-case requirements are open questions in BRIEF.md.

## Next
- Ask the owner to specify zero/negative/non-integer input behavior (BRIEF.md open questions).
- Done when: SPEC.md states it, a test asserts it, and `verify.py run --strict` + `status` print green.


<!-- file written by the agent: fixture/FEATURES.md -->
# FEATURES

What the library offers and how each feature is reached. `features.py check --strict` tests
every entry point against the code. No routes, UI or CLI exist. Out of scope: the live payment gateway
(named in AGENTS.md and VERIFY.md) is not in this project.

## Checkout fee
- what: Return the checkout total: the supplied price in cents plus a fixed 10-cent fee.
- api: `total(cents)` @ app.py :: def total(cents)
- trace: `def total` @ app.py > `cents + 10` @ app.py
- effect: return value only; no state, I/O or gateway call.
- requirement: SPEC.md
- verify: Checkout fee
- status: proven: `python -m unittest discover tests` OK on 2026-10-11 (no git, so no commit pin); rejection proven by challenge


<!-- file written by the agent: fixture/docs/architecture.md -->
# Architecture (as-is)

Single-module Python library; no package manifest, dependencies, storage, network or entry script.

```
caller ──total(cents)──▶ app.py: total()  ──▶ returns cents + 10
tests/test_total.py ──imports──▶ app.total
```

## Boundaries
- `app.py` — the whole product: `total(cents)` adds the fixed fee (app.py:1-2).
- `tests/test_total.py` — unittest check of the SPEC.md fee (imports `from app import total`, line 2).
- External: live payment gateway — not in this project (AGENTS.md, VERIFY.md blind spots).

## Placement
- Source at the folder root; tests in `tests/` discovered by `unittest discover`.

## Unknowns
- Who calls `total()` in production and how the gateway receives the total.
- Rationale for the 10-cent fee beyond SPEC.md: unknown.


<!-- file written by the agent: fixture/docs/commands.md -->
# Commands

All run from `fixture/` (this folder). Prerequisite: Python 3 (observed 3.13.4); stdlib only.

| Purpose | Command | Source | Status |
|---|---|---|---|
| Unit tests | `python -m unittest discover tests` | AGENTS.md | ran 2026-10-11: 1 test OK |
| Verification (strict) | `python <verify-loop>/scripts/verify.py run --strict` then `status` | VERIFY.md | ran: green |
| Feature map check | `python <feature-map>/scripts/features.py check --strict` | FEATURES.md | ran: exit 0 |

`<verify-loop>` / `<feature-map>` = the installed top-tier-engineer skills under
`<repo>/skills/`.
No build, launch, CLI, CI or deploy commands exist (AGENTS.md: none requested).
