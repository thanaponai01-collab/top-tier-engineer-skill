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

Show the user every state machine the code holds without saying so, draw each one, and say which
have bugs. Fix only what the user asked you to fix.

**The lens**

Anything that moves through stages is a state machine, whether or not the code says so: an order
that is placed, paid, shipped; a job that is waiting, running, done. Code rarely declares these. It
leaves a status string set in six files and checked in twelve, flags that only make sense in some
combinations, a field whose `None` means "not yet". The bugs live in the gaps between what the code
sets and what it checks: a value checked but never set (a typo, a renamed state), a combination
that should be impossible but can be reached, a state nothing leaves, a move that skips its guard.
Each one is something a real person hits: an order that cannot be refunded, a printer that never
works again. How you find them is up to you: read it all if it fits, search, run it.

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

The top part is for an owner who does not read code: everyday words, each problem said as what
goes wrong for a person using the product. No file names, function names, code or commands above
the `Details` line. Everything a developer or agent needs to act goes below it.

```
Verdict: <one sentence: how many things move through stages, and how many of those are broken>
What I found (most serious first):
- <what goes wrong for a person using it, and when>: fixed | still open
What looked wrong but is fine: <what>: <why, in everyday words>      (or: nothing)
What I did: <what works now that did not before; or: nothing, you did not ask for fixes>
Your call: <the decision that is the owner's, and what each choice means; or: nothing needed>
Pictures: <file the diagrams are in>

Details (for the developer or agent who picks this up)
1. <machine: field(s)> — states: <a, b, c>; final: <c>
   Bug: <what goes wrong, in plain words> (<file:line>): fixed | open
     Proof: `<test command>` (<file:line of the test>) fails on the code as it was
   (one line per bug; one block per machine)
Not bugs: <what looked wrong>: <why it is fine>      (one per lead)
Not machines: <field or flags>: <why: independent, every mix valid>
Fixed: <bug>: <change>; its test passes now        (or: not asked)
Tests: <command>: <n> passed before, <n> passed after
```
