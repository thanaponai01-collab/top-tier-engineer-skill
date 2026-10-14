All eight context categories are now in place in `fixture/`, and the one behavior with a written requirement is verified locally: `VERIFY-STATE: green` from a strict run on the final files. I didn't change any product code, tests or `SPEC.md` (they're byte-identical to the originals). The MANUAL notes in `AGENTS.md` and `VERIFY.md` are kept word for word, with their original line endings.

**What I checked**
- **Project:** a plain Python library with no manifest, lockfile or pinned Python version; I used Python 3.13.4. Everything runs from `fixture/`. The only entry point is `app.total(cents)`; there is no CLI, server, UI or background job.
- **Behavior checked:** `SPEC.md` says the checkout adds a fixed 10-cent fee, and `tests/test_total.py` expects `total(100) == 110`. The spec and the test agree.
- **Commands run:**
  - `python -m unittest discover tests` passed (1 test).
  - I ran a mutation test in a scratch copy, changing `cents + 10` to `cents - 10`. The test caught it with the declared message "expected total 110" (the copy returned 90 instead of 110).
  - I froze the checks, then ran the strict check, the status check and the test-mapping check. All passed.
- **One stale result:** status briefly showed `stale` because I wrote the new documents after the first green run, and status covers every file. The checks themselves hadn't changed. I re-ran the strict check on the final files and it came back green.

| category | file | state | what I did | evidence |
|---|---|---|---|---|
| startup | AGENTS.md | present | refreshed: added one start-here block (16 of 30 lines); everything already there is untouched | *proven*: both structure checkers pass with no issues or gaps |
| intent | BRIEF.md | present | created | *traced*: goal, rules and decisions are each quoted from SPEC.md, AGENTS.md or VERIFY.md; open questions are listed |
| work | BUILD.md | present | created | *proven*: has a Next step with a completion check; handoff check passed |
| features | FEATURES.md | present | created, marked partial | *traced*: `app.total` → `app.py:1-2` → `tests/test_total.py` |
| verify | VERIFY.md | present | refreshed: added a "Checkout total" check and one blind spot; the MANUAL gateway note is kept | *proven*: strict run and status are green; mutation caught |
| architecture | docs/architecture.md | present | created | *traced*: links cite source lines; the gateway is shown as external, with no code link found |
| commands | docs/commands.md | present | created | *proven*: tests and verifier were run; no build, launch or deploy commands exist |
| memory | .project-context/index.sqlite | present | created (6 documents indexed) | *proven*: index check passed and search returns results; it's a lookup aid, not proof of behavior |

**Other files I added**
- `verification/fee-sign.json`: the mutation spec.
- `.verify-state.json`: the verifier's local state.
- `__pycache__/`: left behind by running the tests.

**Gaps**
- **No git repo:** there's no ignore file, so `.project-context/` and `.verify-state.json` aren't git-ignored. I didn't create an ignore file without an existing convention to follow.
- **Owner questions:** the spec doesn't say what `total` should do with zero, negative or non-integer input. That behavior is unverified; only an input of 100 is tested.
- **Payment gateway:** the live gateway is out of scope, as the MANUAL note says, and isn't covered by any check.
- **Coverage:** green covers only this one mapped behavior, not every possible feature.
- **CI:** not set up, since `AGENTS.md` says none was requested.

**Next step** (also in `BUILD.md`): get the owner's answer on input range. Then add a test backed by the spec, and have a person re-freeze the checks before the strict run goes green again.

<!-- file written by the agent: fixture/BRIEF.md -->
# Brief

Goal: a Python library whose checkout `total(cents)` returns the supplied price plus a fixed
10-cent fee. Source: SPEC.md.

## Constraints (in force)
- Amounts are integer cents. Source: AGENTS.md (MANUAL).
- Preserve product behavior and the live gateway note. Source: AGENTS.md.
- No CI or deployment setup requested. Source: AGENTS.md.

## Decisions
- Library only; no CLI, server or UI. Source: AGENTS.md ("This is a Python library").
- The live payment gateway is outside this local project. Source: VERIFY.md (MANUAL).

## Acceptance
- `total(100) == 110` (price + 10-cent fee). Source: SPEC.md; checked by tests/test_total.py.

## Open questions (owner)
- Behavior for zero, negative or non-integer input is unspecified.
- How (and whether) this library talks to the live payment gateway is undocumented here.

A changed decision replaces its line here; keep the source.


<!-- file written by the agent: fixture/BUILD.md -->
# Build

## Current
- Context foundation prepared 2026-10-11. No product code changed.
- Evidence: VERIFY.md "Checkout total" is strict green (`verify.py run --strict`, `status`:
  VERIFY-STATE: green); mutation verification/fee-sign.json was caught with "expected total 110".

## Blockers
- None for local work. Input-range behavior awaits owner answer (BRIEF.md, Open questions).

## Next
- Ask the owner the BRIEF.md open questions on input range; then add spec-backed tests for them.
  Done when: SPEC.md states the rule, a test covers it, and VERIFY.md is strict green again
  after re-baseline by a person.


<!-- file written by the agent: fixture/FEATURES.md -->
# Features (partial map)

Entry-point families: public Python API only. CLI, routes/UI, jobs: none found (fixture/ has
app.py and tests/ only). Integration: live payment gateway, outside this project (not mapped).

| Feature | Requirement | Entry point | Implementation | Check | Evidence |
|---|---|---|---|---|---|
| Checkout total | SPEC.md | `app.total(cents)` | app.py:1-2 | tests/test_total.py (VERIFY.md "Checkout total") | proven: strict green + caught mutation |

Unmapped: input-range behavior (unspecified); gateway integration (external).


<!-- file written by the agent: fixture/docs/architecture.md -->
# Architecture (as-is)

```
caller (Python import)
      |
      v
app.total(cents)  -- app.py:1-2, returns cents + 10
      ^
      |
tests/test_total.py  -- unittest, `from app import total` (line 2)

[ live payment gateway ]  -- outside this project (VERIFY.md blind spot); no code edge found
```

## Boundaries
- `app.py`: the whole library; one pure function, no storage, no I/O, no dependencies.
- `tests/`: unittest suite; imports `app` from the project folder (run from fixture/).

## Placement
- Source at folder root (app.py); tests in tests/test_*.py; mutation specs in verification/.
- Local verifier state `.verify-state.json` and memory cache `.project-context/` are generated.

## Unknowns
- No manifest, lockfile or pinned Python version. Observed with Python 3.13.4.
- Rationale for the 10-cent fee is not recorded beyond SPEC.md.
- How the gateway would call this library is undocumented.


<!-- file written by the agent: fixture/docs/commands.md -->
# Commands

All run from the project folder (fixture/). Prerequisite: Python 3 (observed 3.13.4; no pin,
no third-party dependencies, no manifest).

| Purpose | Command | Source | Status |
|---|---|---|---|
| Unit tests | `python -m unittest discover tests` | AGENTS.md | ran 2026-10-11: OK (1 test) |
| Verify recipe | `python <verify-loop>/scripts/verify.py run --strict` then `status` | VERIFY.md | ran: green |
| Mutation challenge | `python <verify-loop>/scripts/verify.py challenge . --feature "Checkout total" --mutation verification/fee-sign.json` | VERIFY.md | ran: caught |
| Memory search | `python <project-context>/scripts/context.py --repo . search <terms>` | AGENTS.md start-here | see AGENTS.md |

`<verify-loop>` and `<project-context>` are the installed top-tier-engineer skill folders:
`<repo>/skills/`. No build, launch or deploy step exists.
