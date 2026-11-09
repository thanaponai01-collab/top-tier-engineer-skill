---
name: state-machines
description: >-
  Find the state machines a codebase never declared (status strings, flag combinations, fields whose None means "not yet"), draw each one, and prove each bug in them with a test that fails on the code as it was. Use for "find the implicit state machines", "what states can an order be in", "which states are impossible or stuck".
disable-model-invocation: true
metadata:
  stage: review
  card: "find the state machines nobody declared"
---

# State machines

Show the user every state machine the code holds without saying so: a status string set in six
files and checked in twelve, flags that only make sense in some combinations, a field whose `None`
means "not yet". Draw each one as a picture and say in plain words which have bugs. The bugs live
in the gaps: a value checked but never set (a typo, a renamed state), a combination that should be
impossible but can be reached, a state nothing leaves, a move that skips its guard. Fix only what
the user asked you to fix. How you find them is up to you: read it all if it fits, search, run it.

**What done looks like**

- Every write and every check of each status field or flag is accounted for by `file:line`: each
  write is a move in some machine (or a named non-move, such as loading saved data), and each
  written value is one of its states.
- Every value that is checked but never set, and every state nothing leaves, gets a verdict: a bug,
  or the reason it is fine (set from outside data, a state meant to be final).
- Each bug is proven by a test that fails on the code as it was, for the reason named, not on an
  import error. A fixed bug's test passes now and stays in the suite; an open bug's test is kept
  apart so the suite stays green. No test that passed before fails after.
- Each machine is drawn as a diagram (mermaid is fine) with its states and moves, in a file the
  user can open.

**Avoid**

- Calling a move unguarded before looking for guards outside the function: decorators, callers.
- Calling independent flags a machine. Preferences such as email on and SMS on allow every mix.
- Calling a never-set value dead when outside data (an API payload, a saved file) can set it.
- Reporting a bug no test has shown failing.

**The answer**

```
Machines: <file the diagrams are in>
1. <machine: field(s)> — states: <a, b, c>; final: <c>
   Bug: <what goes wrong, in plain words> (<file:line>): fixed | open
     Proof: `<test command>` (<file:line of the test>) fails on the code as it was
   (one line per bug; one block per machine)
Not bugs: <what looked wrong>: <why it is fine>      (one per lead)
Not machines: <field or flags>: <why: independent, every mix valid>
Fixed: <bug>: <change>; its test passes now        (or: not asked)
Tests: <command>: <n> passed before, <n> passed after
```
