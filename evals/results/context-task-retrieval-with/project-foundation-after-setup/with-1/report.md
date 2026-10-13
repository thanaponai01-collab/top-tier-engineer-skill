Every context file now exists for the `fixture/` project, and the 10-cent fee rule is locally verified: the strict run and `status` both report `VERIFY-STATE: green`. `app.py`, `SPEC.md` and `tests/test_total.py` have the same hashes as before I started, and the two MANUAL notes are kept word for word.

**Setup**
- **Project:** a stdlib-only Python library in `fixture/` (`app.py`, Python 3.13.4 observed). There's no manifest, lockfile, Git repo or CI.
- **Requirement checked:** from `SPEC.md`, checkout adds a fixed 10-cent fee, so `total(100)` returns `110`.
- **Failure signal:** `expected total 110`.
- **Rejection proof:** I changed the fee to `cents + 1` in a scratch copy (`verification/fee-mutation.json`). The test failed with `101 != 110 : expected total 110`, so the check catches a wrong fee.

**Commands I ran:**
- `python -m unittest discover tests`: 1 test, OK.
- The fee mutation check: caught.
- Freezing the checks, then the strict run and `status`: green.
- The test-quality check: 1 test, mapped, has a real assertion.
- The FEATURES.md strict check: exit 0.
- The memory index and its check: no issues.
- The foundation check: no issues.
- The handoff check: 0 structural gaps.

| category | file | state | what I did | evidence |
|---|---|---|---|---|
| startup | AGENTS.md | present | refreshed: added one start-here block (24 lines); the MANUAL line and routing block are unchanged | *proven*: foundation check shows no issues; handoff check passes |
| intent | BRIEF.md | present | created from `SPEC.md` and the AGENTS.md notes; lists 3 open questions | *traced* to `SPEC.md` and AGENTS.md; owner hasn't confirmed, so it's partial |
| work | BUILD.md | present | created: current state, blockers, one Next step and how to tell it's done | *proven*: handoff check found the Next step |
| features | FEATURES.md | present | created: 1 feature, marked partial | *proven*: the strict feature check passes. *Traced*: `test_fee` → `total` → `cents + 10` |
| verify | VERIFY.md | present | refreshed: added the "Checkout total" section; title and MANUAL blind spot kept, one blind spot added | *proven*: strict run green, `status` green, mutation caught |
| architecture | docs/architecture.md | present | created: as-is diagram, boundaries, where files go, unknowns | *traced*: `tests/test_total.py:2` → `app.py:1-2` |
| commands | docs/commands.md | present | created: 4 commands, each with its result | *proven*: every listed command was run |
| memory | .project-context/index.sqlite | present | created: indexed once, then re-indexed AGENTS.md after editing it | *proven*: index check shows no issues; it searches context files only, not product behavior |

**Other files I added:**
- `verification/fee-mutation.json`: the wrong-fee change used for the rejection proof.
- `.gitignore`: there were no ignore rules before. It covers the local verification state, the memory index and `__pycache__/` (the test runs leave a `__pycache__/` folder behind).
- `.verify-state.json`: the verifier's local state.

**Gaps:**
- **Edge cases are unchecked:** `SPEC.md` doesn't say what should happen for 0, negative or non-integer prices.
- **The live payment gateway is outside this project**, as AGENTS.md says.
- **Only one feature exists to map.** It's a library with no routes, UI or command line. FEATURES.md lists the function `total(cents)` as its way in.
- **Paths are tied to this machine:** the memory and helper commands in AGENTS.md point at the installed plugin folder, so they break if the plugin moves.

**Next step:** ask the owner what 0, negative and non-integer prices should do. It's done when `SPEC.md` (or BRIEF.md) states the rule and a new check for it has been seen failing, then passes the strict run.

<!-- file written by the agent: fixture/BRIEF.md -->
# Brief

Goal: a small Python checkout library whose total is the supplied price plus a fixed fee.
Authoritative requirement: SPEC.md. Constraints come from AGENTS.md (owner notes).

## Requirements in force
- Checkout total = supplied price + fixed fee of 10 cents. Source: SPEC.md.

## Constraints and decisions
- Amounts are integer cents (AGENTS.md, MANUAL note).
- This is a Python library; checks run with `python -m unittest discover tests` from this folder (AGENTS.md).
- Preserve product behavior; no CI or deployment setup requested (AGENTS.md).
- The live payment gateway is outside this local project (AGENTS.md, VERIFY.md MANUAL note).

## Acceptance
- `total(100)` returns `110` (SPEC.md example rule; checked by tests/test_total.py, see VERIFY.md).

## Open questions (not answered by any owner record)
- Behavior for 0, negative or non-integer prices: unspecified; do not infer from code.
- Whether the fee can ever vary (currency, region, promotions): unspecified; SPEC says "fixed".
- How the library connects to the live payment gateway, and who owns that integration: unknown.

A changed decision replaces its line here; keep the superseded line's source in the commit or a note.


<!-- file written by the agent: fixture/BUILD.md -->
# Build

## Current state (2026-10-13)
- Product: `app.total` implements SPEC.md's fee rule; source unchanged by foundation setup.
- Evidence: VERIFY.md "Checkout total" is strict green (`verify.py run --strict`, `status` green);
  a fee mutation (`cents + 10` -> `cents + 1`, verification/fee-mutation.json) was rejected with
  "expected total 110". Receipts live in the ignored `.verify-state.json`.
- Context: BRIEF.md, FEATURES.md (partial, strict check passes), VERIFY.md, docs/architecture.md,
  docs/commands.md created or refreshed by project-foundation.

## Blockers
- None for local verification. Edge-case inputs (0, negative, non-integer) have no requirement; see BRIEF.md open questions.

## Next
- Ask the owner to answer the BRIEF.md open question on 0/negative/non-integer prices.
  Done when SPEC.md (or BRIEF.md) states the rule and VERIFY.md has a check for it that was seen red, then strict green.


<!-- file written by the agent: fixture/FEATURES.md -->
# Features

Partial map: Python library, no routes, UI, shortcuts or CLI. The only public entry is `app.total`,
reached by callers through `from app import total` (see tests/test_total.py).
Not built here: the live payment gateway (outside this local project, per AGENTS.md and VERIFY.md).

## Checkout total
- what: Return the price in integer cents plus the fixed 10-cent checkout fee (SPEC.md).
- api: `total(cents)` @ app.py :: def total
- trace: `test_fee` @ tests/test_total.py > `total` @ app.py > `cents + 10` @ app.py
- effect: pure return value; no storage, files or requests.
- verify: Checkout total
- status: proven: `python -m unittest discover tests` passed; fee mutation rejected with "expected total 110" (verify.py challenge, 2026-10-13)


<!-- file written by the agent: fixture/docs/architecture.md -->
# Architecture (as-is, traced 2026-10-13)

<!-- context-paths: app.py, tests/test_total.py -->

```
caller (tests/test_total.py, or any importer)
   |  from app import total          tests/test_total.py:2
   v
app.total(cents) -> cents + 10       app.py:1-2
   |
   v
return value (int cents); no storage, no I/O, no network
```

## Boundaries
- `app.py`: the whole library; one pure function `total`. No dependencies beyond Python.
- `tests/`: stdlib `unittest` suite; imports `app` by module name, so tests run from this folder.
- External: live payment gateway is outside this project (AGENTS.md); no code here calls it.

## Placement
- Source at package root (`app.py`), tests in `tests/test_*.py`, specs in `SPEC.md`.
- Verification artifacts: `verification/` (mutation definitions); local state `.verify-state.json` (ignored).

## Unknowns
- No packaging manifest (pyproject/setup.py) or pinned Python version; observed with Python 3.13.4.
- Rationale for the module layout is not recorded; none inferred.


<!-- file written by the agent: fixture/docs/commands.md -->
# Commands

All commands run from this folder (the directory holding `app.py`). Prerequisite: Python 3 (observed 3.13.4); no third-party packages, no manifest or lockfile.

| Purpose | Command | Source | Status (2026-10-13) |
|---|---|---|---|
| Unit tests | `python -m unittest discover tests` | AGENTS.md | ran: 1 test, OK |
| Verify recipe (strict) | `python <verify-loop>/scripts/verify.py run --strict` then `status` | VERIFY.md | ran: VERIFY-STATE green |
| Challenge fee check | `python <verify-loop>/scripts/verify.py challenge . --feature "Checkout total" --mutation verification/fee-mutation.json` | verification/ | ran: caught |
| Feature map check | `python <feature-map>/scripts/features.py check --strict` | FEATURES.md | ran: exit 0 |

`<verify-loop>` and `<feature-map>` are the installed top-tier-engineer skill directories, not part of this project.
No build, launch, CI or deployment commands exist (AGENTS.md: none requested).
