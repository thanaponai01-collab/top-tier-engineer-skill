---
name: cleanup
description: >-
  Clear what agents leave behind (dead code, leftover copies, duplicates, debug prints, litter) without breaking anything, and say what came back since last time. Use for "clean this up", "remove the mess", "find what's redundant".
disable-model-invocation: true
metadata:
  stage: change
  card: "clean up what agents left behind"
---

# Cleanup

Leave the code so the next agent can work in it without being misled. Agents leave things behind:
`_v2`, `_old` and `copy` files, summary and notes files, scratch scripts and debug dumps, orphaned
modules, dead functions, unused imports, the same helper written two or three times, two ways of
doing one job, debug prints, commented-out code, and comments about past changes. Remove what is
redundant, keep everything that is used working, and tell the user in plain words what changed.
The worst of it misleads most: parallel ways of doing one job, swallowed errors, stubs, and answers
hard-coded to pass a test. You clean the mess; reshaping the code (splitting big files, moving
modules) is untangle's job, so name it and leave it. How you find the mess is up to you.

**What done looks like**

- Every piece of mess found is listed by `file:line` and is removed, merged, kept with a reason, or
  reported unchanged. Duplicates are merged into the copy most callers use.
- The tests were run before any change and again after. No test that passed before fails now, and
  no fewer tests run. With no tests, a command that runs the app stands in for them, and the answer
  says so.
- A deleted file's name is written nowhere any more: not in code, config, scripts or docs.
- A record of this cleanup stays in `.cleanup/` (what was deleted, what was left), and a later run
  starts from it and says first what is new since then and what came back after being deleted.

**Avoid**

- Deleting what looks unused but is loaded by name: `import_module` or `require` with a built
  string, a name in a config file, a script the README tells people to run, an entry point.
- Quietly fixing a swallowed error, a stub or a hard-coded answer. Fixing one changes what the
  program does: name each one, fix it only when it is clearly a bug, and then say it changes
  behavior.
- Restructuring, renaming for taste, or touching code that is not mess.
- Calling a test green that was not run after the last change.

**The answer**

```
Since last time: new: <kind file:line>; came back: <file>      (or: no earlier record)
Removed: <what, in plain words> (<file:line>)          (one line each)
Merged: <the copies> into <the one kept> (<file:line>)
Kept though it looked like mess: <file:line>: <why: what uses it>
Found, not changed: <file:line>: <what it does; changes behavior if fixed>
Fixed (changes behavior): <file:line>: <before -> after>       (or: none)
For untangle: <file or pair>: <why it needs reshaping>        (or: none)
Tests: `<command>`: <n> passed before, <n> passed after
```
