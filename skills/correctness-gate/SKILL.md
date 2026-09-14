---
name: correctness-gate
description: >
  Prove built software is correct with evidence, not plausibility. Use before any release/merge/"it's done" declaration, when asked "does this actually work / test this", after build slices, or after a bug fix to prevent recurrence.
---

# Correctness Gate

> **The question:** Is it provably right?  ·  Inputs, outputs and who runs next: `PROTOCOL.md` §4.

## When not to use this

cause of a failure unknown → `debug-protocol`; not connected at all → `wire-check`; "is it wise" → `senior-review`; adversarial abuse cases → `threat-model` derives them, this gate executes and owns them; releasing it → `ship-gate`.

## The job

You are the engineer who treats "it works" as a guess until an **oracle** says otherwise. An oracle
is a written, checkable statement of what correct behaviour is — without one, the tests only prove
the code agrees with itself. You attack the code the way someone who knows it well would, you
measure what your tests would actually catch, and your final verdict marks every claim **(proven)**
or **(trace-only)** (per `PROTOCOL.md`).

## Steps: Surface → Oracle → Attack → Measure → Verdict

### Phase 1 — Surface

Enumerate what is being gated: the behaviors added or changed since the last gate, the invariants
they touch, and the contracts they participate in. Anything that changed but is not on this list gets past
the gate — so build the list from the diff and the slice reports, not from memory.

### Phase 2 — Oracle

For each behavior, write down how correctness is decided, in order of preference:

1. **From the spec** — the acceptance criterion from the brief. Best of the four: it was written to
   be provable either way.
2. **From the contract** — the module contract in the architecture (data shape, error behaviour, who
   may call it).
3. **From a property** — something that must hold for every input (a round-trip returns the
   original, a total is conserved, order is kept, running it twice changes nothing more than once).
   These catch the most in AI-written code, because they catch wrong outputs nobody thought to
   check, which is exactly what example tests miss.
4. **From a reference** — compare against a trusted implementation, or against output recorded when
   it was known to be right.

A behavior with no oracle available is reported as **untestable as specified** and sent back to
`problem-framing`. Do not invent an oracle that just describes what the code already does — that
tests the code against itself, which is the classic fake test.

**Concurrency is enumerated, not implied** (DECISION_LEDGER D005): where the surfaced behavior
touches something more than one caller can reach at the same time (a shared file, row, counter,
lock, queue slot), write the check-then-claim sequence down as its own property row — "the claim
happens in one step; a second caller arriving at the same time sees either the before state or the
after state, never a half-written one" — instead of quietly folding it into the generic
"concurrent" case in Phase 3. A race is exactly the kind of bug nobody writes down as a criterion
until it happens in production; writing the row is what makes Phase 3's hostile tests actually hit
it.

### Phase 3 — Attack

Build the test suite as an adversary, in this priority order:

1. **Invariant tests** — one per invariant in the brief. These are the rules the suite exists to
   hold.
2. **Property tests** — generate inputs, assert properties. Prefer these wherever an oracle from
   class 3 exists.
3. **Edge and hostile tests** — empty, as large as allowed, malformed, concurrent, unicode, and
   whatever a malicious or confused caller (human or AI) would send. Where the system has a real trust
   boundary, the *adversarial* abuse cases are derived by `threat-model` and handed here as test
   specs; this gate **executes and owns them as regressions** but does not derive the threat model
   itself — that division keeps the security pipeline in one place (Law 1).
4. **Regression tests** — one per bug ever found, named after the bug. A bug fixed with no test
   pinning the fix will come back.
5. **Example tests** — ordinary cases, last, because they catch the least.

For every error path the code claims to handle: trigger it and assert the *structured* failure
(correct error shape, no partial writes, no silent fallback).

### Phase 4 — Measure

Tests passing is necessary, not sufficient — measure whether the suite can actually detect breakage:

- **Mutation spot-check**: introduce 3–5 deliberate small breaks (flip a comparison, drop an error
  branch, off-by-one a boundary) in the riskiest code; the suite must catch each. Revert all
  mutations **(proven by re-running the clean suite)**. A mutation that survives reveals a blind
  spot — close it before the gate passes.
- **Coverage is evidence, never a target**: report the uncovered parts that contain real logic, and
  ignore the percentage. Chasing the number produces tests that assert nothing, which are worse
  than no tests because they make you feel safe.
- **Look at the real thing**: besides the assertions, run a handful of real or realistic inputs end
  to end and *read the output yourself*. Reading ten real outputs catches whole kinds of wrongness
  that tests miss, because a test only checks what someone thought to check. Paste one
  representative input→output pair into the verdict to show this was done.
- **Unreliable tests come out**: a test that passes and fails with no code change is removed from
  the gate and written down as deferred work with the trigger "before next gate". Never just re-run
  it until it goes green.

### Phase 5 — Verdict

The verdict goes inline in the report — a file only when §3 warrants one, overwritten
each gate (history is in version control):

1. Verdict line — a `GATE` line per PROTOCOL §5, its state carrying the §1 tag.
2. Director summary — three sentences, plain language: what was proven, what was only reasoned,
   what risk remains.
3. Behavior table — `behavior | oracle class | result | evidence tag`.
4. Mutation results, quarantined flakes, untestable-as-specified items.
5. Residual risk — the honest list of what this gate cannot see (environments not run, scales not
   reached, integrations stubbed).

A **fail** names why each failure happened (missing oracle, wiring gap, logic error, framing error)
so the fix goes to the right skill — connection problems to `wire-check`, unknown causes to
`debug-protocol`. And separate a real break from an unfamiliar approach: code that breaks an oracle
fails; code that merely surprises you gets a question, not a rewrite.

## Rules

- No gate passes on **(trace-only)** evidence alone if the environment permits execution.
- Tests are production code: same naming, same conventions, same review standard.
- Never weaken an oracle to make a gate pass; oracle changes route through `problem-framing`
  (criteria) or `arch-design` (contracts) with the director's confirmation.

## Common mistakes

Tests that assert what the code does instead of what it should do; "looks right to me" used as a
gate.
