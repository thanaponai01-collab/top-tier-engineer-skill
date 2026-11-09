---
name: untangle
description: >-
  Untangle a codebase where its history says changes hurt, keeping behavior the same. Use for "untangle this", "clean up the structure so the next change is easier".
disable-model-invocation: true
metadata:
  stage: change
  card: "untangle it where changes hurt"
---

# Untangle

Make the next change cheaper. The next person to change this code, most likely an agent, should
spend less effort finding what to change, break less without noticing, and find a bug's cause
faster. What the program does stays the same. Untangle where the git history says changes land and
fixes repeat: files with many commits and many fix commits, and files that keep changing together.
A tangle that is easy to see but that nothing ever changes is not the target. How you read the code
and what you move are up to you.

**What done looks like**

- Each file that changes and gets fixed most, and each pair that keeps changing together, is a
  target (with the commits that show what it costs) or skipped with a reason. A file where a third
  or more of its commits are fixes has a tangle inside it; skip it only if a test already catches
  each of its recent fixes being undone.
- The tests were run on the committed tree before any change. Tests already red then are each
  sorted as environment, stale, or a real bug, with the evidence. A red test caused by a real fault
  is a bug, not a stale test. A bug gets a `untangle: known bug: <symptom>` comment next to the
  fault, where the next person debugging will look.
- Every changed file serves a target. Each move has a test that passes now and would fail if the
  tangle came back, or says why there is none.
- The same tests run after: no test that passed before fails now, and no fewer tests run.

**Avoid**

- Fixing a bug found along the way. It changes behavior: mark it and name it first in the answer.
- Undoing a past fix while moving code. Each fix in the history was there for a reason.
- Picking tangles by how they look (import direction, layers, copied helpers) when the history
  shows the pain elsewhere. Clearing dead code and litter is cleanup's job.
- Calling a test green that was not run after the last change.

**The answer**

```
Known bugs (not fixed): <file:line>: <symptom>                  (or: none)
Targets: <file or pair>: <commits that show the cost> -> <what changed>  (one line each)
Skipped: <file or pair>: <why it does not hurt>
Red before: <test>: env | stale | bug: <evidence>               (or: none)
Guards: <target>: `<command>` passes now, fails on the old tree  (or: none: <why>)
Tests: `<command>`: <n> passed before, <n> passed after, nothing green went red
```
