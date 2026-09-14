---
name: correctness-gate
description: Prove built software is correct with evidence, not plausibility. Use before any release, merge or "it's done", when asked "does this actually work / test this", after building a feature, or after a bug fix to stop it coming back.
---

# Correctness Gate

"It works" is a guess until an **oracle** says otherwise. An oracle is a written, checkable
statement of correct behavior. Without one, tests only prove the code agrees with itself. Attack the
code like someone who knows it well, measure whether the tests would actually catch breakage, and
mark every claim proven, traced or suspected.

## Phases

### 1. Surface
List what's being gated: behaviors added or changed, the requirements they touch, the contracts they
take part in. Build the list from the diff, not memory. Anything missing from it slips past.

### 2. Oracle
For each behavior, decide how correctness is judged, in order of preference:
1. **Spec:** an acceptance criterion written to be provable either way.
2. **Contract:** the documented data shape, error behavior, who may call it.
3. **Property:** something true for every input (round-trip returns the original, totals are
   conserved, order is kept, running twice = running once). These catch the most in AI-written
   code, because they catch wrong outputs nobody thought to check.
4. **Reference:** a trusted implementation, or output recorded when known good.

No oracle available → report the behavior as **untestable as specified** and say what criterion is
missing. Never invent an oracle that just describes what the code already does.

**Write concurrency down explicitly.** Where two callers can reach shared state at once (a file,
row, counter, lock, queue slot), write the check-then-claim as its own property: "a concurrent
caller sees the before state or the after state, never half of it."

### 3. Attack
Build tests as an adversary, in this priority order:
1. **Invariant tests:** one per requirement that must never break.
2. **Property tests:** generated inputs, asserted properties.
3. **Edge and hostile tests:** empty, maximum size, malformed, concurrent, unicode, whatever a
   confused or malicious caller would send.
4. **Regression tests:** one per bug ever found, named after the bug.
5. **Example tests:** ordinary cases, last, because they catch the least.

For every error path the code claims to handle: trigger it and assert the structured failure
(correct error shape, no partial writes, no silent fallback).

### 4. Measure the tests
- **Mutation spot-check:** make 3–5 deliberate small breaks in the riskiest code (flip a comparison,
  drop an error branch, shift a boundary by one). The suite must catch each. Revert and re-run
  clean. A surviving mutation is a blind spot to close before passing.
- **Coverage is evidence, not a target.** Report uncovered code that holds real logic; ignore the
  percentage.
- **Look at real output.** Run a handful of realistic inputs end to end and read the results
  yourself. Include one input → output pair in the report.
- **Flaky tests come out** of the gate and get noted for fixing. Never re-run until green.

### 5. Verdict
- Open with pass or fail and the one reason that decided it.
- What was proven, what was only reasoned, and what this gate can't see (environments not run,
  scale not reached, integrations stubbed).
- A table: behavior, oracle type, result, proven / traced / suspected.
- Mutation results and anything untestable as specified.

A failure names why: missing oracle, not wired, logic error, or wrong requirement. Code that breaks
an oracle fails; code that merely surprises you gets a question, not a rewrite.

## Rules

- Don't pass on reading alone if the environment can run the tests.
- Tests are production code: same naming, conventions, review standard.
- Never weaken an oracle to make the gate pass. Changing a criterion needs the owner's agreement.

## Common mistakes

Tests that assert what the code does instead of what it should do; "looks right to me" as a gate.
