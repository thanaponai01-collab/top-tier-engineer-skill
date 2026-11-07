---
name: dependency-health
description: >-
  Find what a repo's dependencies owe (known security holes, also in packages pulled in by others; end-of-life runtimes; lockfiles out of step; packages nothing uses), fix it without breaking anything, and say what is new since last time. Use for "are our dependencies healthy?", "check the dependencies", "anything outdated or vulnerable?".
disable-model-invocation: true
metadata:
  stage: change
  card: "pay what the dependencies owe"
---

# Dependency health

**Goal:** every dependency problem worth acting on is fixed, removed, or accepted on purpose with a
reason and a date to look again, and nothing that worked breaks. Tell the user in plain words, worst
first. A large upgrade that needs code changed across the project is evolve-maintain's job: name it.
`D` is `python <this skill's base directory>/scripts/deps.py <repo>`, run from the repo root.

1. `D --run "<test cmd>"` before you change anything. It writes `.deps/findings.md`: known holes
   (from OSV.dev, or `--advisories FILE`), end-of-life runtimes, lockfile drift, unused packages,
   exact pins with no reason, and a **Not checked** list. With a record from an earlier run it lists
   what is new and which accepted findings are due again; put that first in the answer.
2. Read the findings against the code, then fix. "Unused" is a lead: a package can be used with no
   import (a server the Dockerfile runs, data a standard module reads, a plugin loaded by name). A
   pin with a reason in a comment may guard code that a newer version breaks: read that code before
   moving it, and either change the code too or leave the pin. Change the manifest, then regenerate
   the lockfile with the project's own tool (`pip-compile`, `uv`, `npm install`), never by hand where
   the lock holds hashes. A major-version jump the tests do not cover is named as a behavior change.
3. A high finding you leave as it is: `D --accept ID --reason "..." --until YYYY-MM-DD`. Leaving a
   known security hole is the user's call: say so in the answer.
4. `D --done`. It refuses while a high finding is neither fixed nor accepted, a test that passed now
   fails, fewer tests run, or a manifest changed while its lockfile did not. Fix the cause, never the
   check. It saves `.deps/history.json` and prints `DEPS: done`.

Never call an ecosystem healthy that sits under **Not checked**: say what was not checked and why.

The answer, in plain words: new since last time (if a record exists), fixed (package old -> new,
and why it mattered), removed, kept though it looked unused (and why), accepted or for the user to
decide, not checked. Leave `.deps/` in place: the next run compares against it.
