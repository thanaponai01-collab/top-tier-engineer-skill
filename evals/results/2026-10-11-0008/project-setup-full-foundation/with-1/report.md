The foundation is ready and the local check is green. It covers only the single 100→110 fee case. `app.py` and `tests/` are unchanged.

I used the foundation procedure from drive. The project is one function, so I worked inline with no workers and no RUN.json. There was no feature to build, and I treated RUN.json as unnecessary for this.

**Evidence**
- **Proven:** `python -m unittest discover tests` passes.
- **Proven:** `verify.py run . --strict` is green and `status` reports green.
- **Proven:** I changed the fee from +10 to +11 in a scratch copy. The check failed with "expected total 110", so the check does reject a wrong fee. The mutation file is `verification/fee_mutation.json`.
- **Proven:** `foundation.py check` reports no issues, and `context_budget.py --check-handoff` reports 0 structural gaps.
- **Proven:** The project-memory index was built and its structural check is clean.
- **Not proven:** `foundation.py` still reports freshness as "unknown; no setup snapshot", even though I recorded a snapshot. I didn't investigate why.

**Created**
- `BRIEF.md`: constraints and decisions from `AGENTS.md` and `SPEC.md`, plus open questions.
- `BUILD.md`: current state and one Next step.
- `FEATURES.md`: a partial map with one feature.
- `docs/architecture.md` and `docs/commands.md`: both traced from the code.
- `verification/fee_mutation.json` and `.gitignore`.
- `.verify-state.json` and `.project-context/` also exist now. Both are ignored.

**Refreshed**
- `VERIFY.md` now has a "Checkout fee" check with a fail signal and fail proof. I added one blind-spot line.
- `AGENTS.md` got a start-here block, which I appended.

**Kept**
- The `AGENTS.md` MANUAL integer-cents note and the live-gateway note, both verbatim.
- `SPEC.md`, `app.py` and the test.

**Outside coverage**
- **Gateway:** The live payment gateway isn't covered. This is a recorded blind spot.
- **Inputs:** Zero, negative and non-integer inputs have no stated requirement, so they are unverified. They are listed as open questions in `BRIEF.md`.
- **Callers and packaging:** Nothing in the repo calls `total`, and there is no packaging, so those are unknown.
- **CI and deployment:** CI was not requested, so none was set up. No commits or releases were made, and the folder isn't a git repository.
- **Design rationale:** Why it is built this way isn't recorded, so I didn't write it.

**Next:** get the owner's answers on input handling, then add a test backed by those requirements. This is written in `BUILD.md`.

<!-- file written by the agent: fixture/BRIEF.md -->
# Brief

Goal: a small Python library whose checkout total adds a fixed fee to a price in integer cents.

## Constraints and decisions in force
- Amounts are integer cents. (source: AGENTS.md, MANUAL)
- Fee is a fixed 10 cents added to the supplied price. (source: SPEC.md)
- Run tests with `python -m unittest discover tests` from this folder. (source: AGENTS.md)
- No CI or deployment setup requested; preserve product behavior. (source: AGENTS.md)
- The live payment gateway is outside this project. (source: VERIFY.md, MANUAL)

## Acceptance
- `total(100) == 110` (source: SPEC.md fee rule; tests/test_total.py)

## Open questions (owner has not said)
- Behavior for zero, negative or non-integer input.
- Whether the fee ever varies by amount or gateway.
- Where the library is consumed from (no packaging or caller exists here).


<!-- file written by the agent: fixture/BUILD.md -->
# Build

## Current state
- `app.total` and one test exist; test passes (proven, 2026-10-11).
- Foundation prepared: BRIEF, FEATURES, VERIFY (strict green, mutation caught), docs/architecture.md, docs/commands.md.
- Blockers: none for local work. Input edge cases and the live gateway are unspecified/out of scope.

## Next
Get the owner's answer to the open input questions in BRIEF.md, then add a requirement-backed test.
Completion check: `python <verify-loop>/scripts/verify.py run . --strict` is green with the new case.


<!-- file written by the agent: fixture/FEATURES.md -->
# Features (partial map)

| Feature | Requirement | Entry point | Implementation | Check | Evidence |
|---|---|---|---|---|---|
| Checkout fee | SPEC.md | `app.total(cents)` | app.py:1-2 | tests/test_total.py via VERIFY.md "Checkout fee" | proven: strict green, +11 mutation caught |

Unmapped: no other entry points exist (single function, no CLI/API/jobs). Unverified: non-100 inputs, gateway.


<!-- file written by the agent: fixture/docs/architecture.md -->
# Architecture (as-is, traced)

```
caller (none in repo) --> app.total(cents)  [app.py:1]  --> cents + 10 (fee)
tests/test_total.py ----> app.total
```

- One module, no storage, no external dependencies, no entry points besides the function.
- Fee rule source: SPEC.md. Payment gateway: outside the project (VERIFY.md blind spot).
- Unknowns: who calls `total`; packaging; reasons for the design (not recorded).


<!-- file written by the agent: fixture/docs/commands.md -->
# Commands

All run from the project folder (`fixture/`); Python stdlib only, no install step.

| Purpose | Command | Source | Status |
|---|---|---|---|
| Unit tests | `python -m unittest discover tests` | AGENTS.md | ran, passes |
| Strict verification | `python <verify-loop>/scripts/verify.py run . --strict` | VERIFY.md | ran, green |

No build, launch, CI or deploy commands exist.
