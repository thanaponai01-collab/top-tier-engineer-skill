---
name: correctness-gate
description: >
  Prove built software is correct with evidence, not plausibility. Use before any release, merge or "it's done", when asked "does this actually work / test this", after building a feature, or after a bug fix to stop it coming back.
---

# Correctness Gate

"It works" is a guess until an **oracle** says otherwise. An oracle is a written, checkable
statement of correct behavior. Without one, tests only prove the code agrees with itself. Attack the
code like someone who knows it well, measure whether the tests would actually catch breakage, and
mark every claim proven or traced.

## How to work

A senior engineer is expensive for what they check, not for how much they say. These are the habits,
each with the test that shows you did it. Scale them to the stakes: a typo needs none of the ritual,
a migration needs all of it.

**1. Understand before you change.** Read the code the work touches and trace the real flow from its
entry point. For a bug, reproduce it first. Before editing a function, find every caller: the fix
belongs where they all route through. Say in one line what you read the request as (and not as); if
two readings lead to different work, ask the one question that separates them and keep working on
what it doesn't block.
*Test:* you can name the files involved and the observation that would prove you wrong.

**2. Ground truth over memory.** Check APIs, versions, config and behavior against the installed
code, `--help`, the lockfile, or a run. Anything remembered is an assumption until looked at.
*Test:* every fact the work rests on came from something you opened or ran in this session.

**3. Decide what done looks like first.** Turn the task into a check: "fix the bug" → a repro that
fails, then passes; "refactor" → the same tests green before and after; "is it secure" → the abuse
case that now fails. Loop until the check passes. Never weaken the check to get there.
*Test:* the check was written down before the work started.

**4. Smallest change that holds.** No features, options or abstractions nobody asked for; an
abstraction earns its place on the second real use. Boring beats clever. Match the existing style,
leave adjacent code alone, and mention unrelated problems instead of fixing them. Clean up only what
your own change orphaned.
*Test:* every changed line traces to the request.

**5. Size the risk before the move.** Ask what breaks if you're wrong and whether it can be undone.
Reversible: move fast. One-way (deleted data, sent messages, deploys, public APIs): slow down and
confirm first.
*Test:* you can state the rollback in one sentence, or you asked before acting.

**6. Stop when you're guessing.** A second failed attempt on the same idea means your model of the
system is wrong. Go back to step 1 and re-check the assumption instead of trying a third variation.
*Test:* each attempt tested a different hypothesis.

**7. Say how you know, briefly.** Answer first: the verdict in plain words, evidence after. Label
claims *proven* (you ran it), *traced* (you read the whole chain) or *suspected* (neither); a clean
result names what you checked. Disagree in one line, then do what was asked, unless the step can't be
undone or would fake the result: then stop and ask.
*Test:* a busy reader can act on your first two lines. Cut words, never verification.

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
- A table: behavior, oracle type, result, proven or traced.
- Mutation results and anything untestable as specified.

A failure names why: missing oracle, not wired, logic error, or wrong requirement. Code that breaks
an oracle fails; code that merely surprises you gets a question, not a rewrite.

## Rules

- Don't pass on reading alone if the environment can run the tests.
- Tests are production code: same naming, conventions, review standard.
- Never weaken an oracle to make the gate pass. Changing a criterion needs the owner's agreement.

## Common mistakes

Tests that assert what the code does instead of what it should do; "looks right to me" as a gate.
