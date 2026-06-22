---
name: correctness-gate
description: >
  Prove that built software is correct — not plausible, not reviewed-and-it-looked-fine, but
  verified against an explicit definition of correct. Use this skill before any release, merge,
  or "it's done" declaration; whenever the user asks "is this right / does it actually work /
  test this"; after any build session completes its slices; and whenever a bug was fixed (to prove
  the fix and prevent recurrence). This is the verification counterpart to senior-review: that
  skill judges wisdom and design quality, this one establishes correctness with evidence.
---

# Correctness Gate

> **Wiring** — Stage 4 of the lifecycle. Consumes: acceptance criteria from `PROBLEM_BRIEF.md`,
> contracts from `ARCHITECTURE.md`, slice proof lines from `build-discipline`. Produces:
> `CORRECTNESS_VERDICT.md` + the test suite. Downstream: `perf-optimize` and ship; runs in
> parallel with `senior-review` at ship time — proof and wisdom are different gates and neither
> substitutes for the other. Shared vocabulary and laws: `PROTOCOL.md` at the suite root —
> authoritative when present.

## Operating contract

You are the engineer who treats "it works" as a hypothesis until an **oracle** says otherwise. An
oracle is an explicit, checkable definition of correct behavior — without one, testing is theater.
You attack the code as its most informed adversary, you measure what your tests actually catch,
and your final verdict distinguishes **(proven)** from **(trace-only)** (per `PROTOCOL.md`) on
every claim.

## Pipeline: Surface → Oracle → Attack → Measure → Verdict

### Phase 1 — Surface

Enumerate what is being gated: the behaviors added or changed since the last gate, the invariants
they touch, and the contracts they participate in. Anything changed-but-unlisted here escapes the
gate — so derive the list from the diff and the slice reports, not from memory.

### Phase 2 — Oracle

For each behavior, write down how correctness is decided, in order of preference:

1. **Specification oracle** — the acceptance criterion from the brief (best: it's falsifiable by design).
2. **Contract oracle** — the module contract from the architecture (shape, error behavior, who-may-call).
3. **Property oracle** — an invariant that must hold for all inputs (round-trips, conservation,
   ordering, idempotency). Properties are the highest-leverage oracles for AI-generated code,
   because they catch the *unanticipated* wrong outputs that example-based tests miss.
4. **Reference oracle** — comparison against a trusted implementation or recorded known-good output.

A behavior with no available oracle is reported as **untestable-as-specified** and routed back to
`problem-framing` — do not invent an oracle that merely matches what the code currently does
(that tests the implementation against itself, the canonical fake test).

### Phase 3 — Attack

Build the test suite as an adversary, in this priority order:

1. **Invariant tests** — one per brief invariant. These are the suite's constitution.
2. **Property tests** — generate inputs, assert properties. Prefer these wherever an oracle from
   class 3 exists.
3. **Boundary & hostile tests** — empty, maximal, malformed, concurrent, unicode, the input a
   malicious or confused actor (human or AI agent) would send. Where the system has a real trust
   boundary, the *adversarial* abuse cases are derived by `threat-model` and handed here as test
   specs; this gate **executes and owns them as regressions** but does not derive the threat model
   itself — that division keeps the security pipeline in one place (Law 1).
4. **Regression tests** — one per bug ever found, named after the bug. A fixed bug without a
   regression test is a bug on layaway.
5. **Example tests** — ordinary cases, last, because they catch the least.

For every error path the code claims to handle: trigger it and assert the *structured* failure
(correct error shape, no partial writes, no silent fallback).

### Phase 4 — Measure

Tests passing is necessary, not sufficient — measure whether the suite can actually detect breakage:

- **Mutation spot-check**: introduce 3–5 deliberate small breaks (flip a comparison, drop an error
  branch, off-by-one a boundary) in the riskiest code; the suite must catch each. Revert all
  mutations **(proven by re-running the clean suite)**. A mutation that survives reveals a blind
  spot — close it before the gate passes.
- **Coverage as evidence, never as goal**: report uncovered regions that contain logic, ignore the
  percentage. Chasing a number produces assertion-free tests, which are worse than no tests because
  they manufacture false confidence.
- **Look at the real thing**: beyond assertions, run a handful of real or realistic inputs
  end-to-end and *read the actual outputs*. Eyeballing ten real outputs catches categories of
  wrongness that tests encode around, because tests only check what someone thought to check.
  Paste one representative input→output pair into the verdict as evidence this was done.
- **Flake quarantine**: a test that passes and fails without code changes is removed from the gate,
  logged in `TODO_LEDGER.md` with trigger "before next gate", and never silently retried-until-green.

### Phase 5 — Verdict

Produce **`CORRECTNESS_VERDICT.md`** (overwritten each gate; history is in version control):

1. Verdict line — `GATE: pass (proven) | pass (trace-only: reasons) | fail (behaviors, evidence)`.
2. Director summary — three sentences, plain language: what was proven, what was only reasoned,
   what risk remains.
3. Behavior table — `behavior | oracle class | result | evidence tag`.
4. Mutation results, quarantined flakes, untestable-as-specified items.
5. Residual risk — the honest list of what this gate cannot see (environments not run, scales not
   reached, integrations stubbed).

A **fail** names why each failure happened (missing oracle, wiring gap, logic error, framing error)
so the fix lands in the right lifecycle skill — wiring gaps route to `wire-check`, unknown causes
route to `debug-protocol` — and distinguishes violations from deviations: code that breaks an
oracle fails; code that merely surprises you gets a dialogue, not a rewrite.

## Rules

- No gate passes on **(trace-only)** evidence alone if the environment permits execution.
- Tests are production code: same naming, same conventions, same review standard.
- Never weaken an oracle to make a gate pass; oracle changes route through `problem-framing`
  (criteria) or `arch-design` (contracts) with the director's confirmation.

## Anti-patterns this skill exists to kill

Tests that assert what the code does instead of what it should do; green suites that catch nothing;
retry-until-green flake handling; coverage worship; "looks correct to me" as a gate; fixed bugs
with no regression tests.
