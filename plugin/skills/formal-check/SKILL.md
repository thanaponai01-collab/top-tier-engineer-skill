---
name: formal-check
description: >-
  Prove a property for every case, not just the ones tested, and keep that proof true to the code. Use for races, retries, state machines, parsers or unsafe code where tests miss the case that breaks: "model-check this", "prove this invariant", "can these steps happen in a bad order?", "is the model still true to the code?"
disable-model-invocation: true
metadata:
  stage: prove
  card: "tests pass, but every order of steps?"
---

# Formal Check

Tests prove things by example, and races, retries, state machines and parsers break on the case
nobody wrote. Pick the promise in this code whose break would hurt users most and that tests
rarely reach, not the easiest one to verify, and check it for every case within a stated scope.
Then leave the check in the repo so the next agent can rerun it and see at once when the code has
moved away from it. Choose the tool the question needs: whether steps can happen in a bad order
suits a model checker over a small model (TLA+ is a good default); whether the code behaves for
every input suits a verifier that runs on the code itself (Kani, CBMC, Dafny, CrossHair) or, where
none runs on this language, generated inputs against the real code (Hypothesis, fast-check). The
tool is the repo's dependency. How you model, map and run it is up to you.

**What done looks like**

- The property and the harm when it breaks are each one plain sentence, with the `file:line` of
  the promise in the code.
- Every part of the model points at a line that exists in the code it covers, and what the model
  treats as one step is one step in the code. Every covered file is mapped.
- The check is one command that exits 0 when the property holds. It passes on the code, and it
  was seen failing with one edit to the code (never the model) that makes the property false.
  If it cannot fail, it proves nothing.
- It runs in minutes, not hours, so people rerun it; if the repo has CI, the same command runs
  there.
- The check, its model, the bounds and assumptions, and the commit it was last true to are kept
  in the repo (for example under `.formal/`), committed, so a later change to the covered code
  shows as stale until someone looks at each commit since and reruns it.
- When checking an existing model: update it from the code, not from what makes it pass; after
  the update the break must fail again. A failure is drift if one of its steps cannot happen in
  the code, and a bug if every step can.

**Avoid**

- Weakening the property, shrinking the bounds or adding an assumption to make a failure go away.
  If any of them change, say so with the reason and the commit or line that justifies it.
- Calling a pass a proof of the whole system. It covers the model, within its bounds.
- Fixing product code. A bug found here goes to debug-protocol if it is installed, or to the user,
  told as the steps that lead to it in the code's words.
- Changing product files to run the check; runs and breaks happen in throwaway copies.

**The answer**

```
<name>: in-sync | updated | bug | blocked | stale
  Property: <one sentence>   Harm: <one sentence>   Target: <file:line>
  Tool: <name version>, because <why this tool fits the question>
  Check: `<command>` passes; fails with <file>: `<old>` -> `<new>`; <seconds>s; CI: yes | no | no CI
  Bounds: <what the run is limited to>   Assumes: <what it takes for granted>
  Changed: <property/bounds/assumes change, with evidence>          (or: none)
  Steps: <what happens> <file:line>, ...                            (bug only, two or more)
  Blocked: <the command that failed and why>                        (blocked only)
Not covered: <what the bounds, the model and the assumptions leave out>
```
