---
name: evolve-maintain
description: >-
  Change a running system without breaking it: upgrades, deprecations, removing an old API, large refactors. Every command and job that reads what changed does what it did before, unless asked otherwise. Use for "upgrade X", "refactor this module", "remove the old endpoint".
disable-model-invocation: true
metadata:
  stage: build
  card: "upgrade, refactor or deprecate on a live system"
---

# Maintenance & Evolution

Make the change asked for, and leave every feature that reads what changed doing what it did
before, unless the user asked for that feature to change too. The break to look for is far from the
edit: a command, scheduled job or config line that reads the changed name, and that no test runs.
How you find the readers and make the change is up to you: read it all if it fits, search, run it.

**What done looks like**

- Before the first edit, the commands users and jobs really run were run on the code as it was,
  and what each printed and every file it wrote were kept somewhere the edit cannot touch.
- Every reader of a name the change touched (a function, a script, a config or job line, a route
  string) was exercised by one of those commands, or the answer says why the change cannot reach
  what it does. "A test covers it" is not a reason unless that test runs the real way in.
- After the change, the same commands were rerun. Each prints and writes what it did before; a
  difference the user asked for is named as asked for, and any other difference is a break, fixed
  before the answer. Reverting is a fix.
- Nothing is deleted until it is shown that nothing loads it (`latent-audit` does this, when it is
  installed). When a break's cause is unclear, prove it before fixing it (`debug-protocol`, when
  installed).

**Avoid**

- Trusting a code search for callers. Config files, job definitions, names built at runtime and
  other repos call code no import shows.
- Comparing only stdout. A cached value can leak into a file the command writes, a backup or an
  export, while what it prints looks the same.
- Calling the change safe because the suite is green. The suite shows only what it runs.
- Throwing the "before" runs away with a scratch copy, so there is nothing left to compare against.

**The answer**

```
Changed: <what was changed, in one line>
Before: `<command>` (one per command users or jobs run; what it printed and wrote is kept at <where>)
Readers: <file:line or job>: exercised by `<command>`   (or: out: <why the change cannot reach it>)
After: `<command>`: same output and files | intended: <what differs and why> | broke: <what>, fixed by <how>
Not checked: <readers, commands or environments no run here covered>
```
