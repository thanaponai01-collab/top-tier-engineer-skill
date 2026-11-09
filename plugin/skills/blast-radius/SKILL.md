---
name: blast-radius
description: >-
  Find what a change breaks outside its diff, and prove the one fact it is safe because of. Use for "what else does this break?", "who depends on this?", "is this change safe?"
disable-model-invocation: true
metadata:
  stage: prove
  card: "it works, but what did it break?"
---

# Blast Radius

A change can do what it meant and still break code it never touched: a caller that passes the old
arguments, a reader of a JSON key or column it renamed, a script that reads an env var or flag it
dropped. Find every consumer of what the diff changed, outside the diff, and say for each whether
it breaks. Most risky-looking changes are safe because of one fact ("this only drops cache entries
that are already dead"); find that fact and prove it, rather than listing maybes. How you find the
consumers and the fact is up to you.

**What done looks like**

- Everything the diff changed is listed: functions whose signature, body or existence changed, and
  every name the diff no longer writes (dict keys, JSON fields, columns, env vars, flags, CLI
  options). Each is searched by its literal name in every tracked file, not just by symbol, so a
  use in a string, a config file or another language is found.
- Every consumer outside the diff has a verdict: `breaks`, `cleared` or `unknown`. `breaks` and
  `cleared` cite the `file:line` (in the repo or in the library's source) they rest on; `unknown`
  says what it depends on. Consumers outside the repo (other services, other repos) are `unknown`,
  naming what they depend on.
- The change is called `safe` only when no consumer breaks and the one fact it is safe because of
  has a proof: a command that passes on the change and fails on a copy with that fact broken. The
  answer names that break.
- The answer states how sure it is: 1 said so, 2 cited `file:line`, 3 walked the failure through
  the lines, 4 ran the proof failing and passing, 5 showed the same in the running app. Below 4 it
  says `unproven`.

**Avoid**

- Changing the product tree. Proofs and breaks run on throwaway copies; fixing what breaks is a
  separate task.
- A proof that passes with the fact broken too: it cannot fail, so it proves nothing.
- Stopping at callers a symbol search finds. The breakage it misses is the point.
- A level higher than what was actually run.

**The answer**

```
Verdict: safe | breaks | unproven
Changed: <function or name>: <how>                               (one line each)
Consumers: <file:line>: breaks | cleared | unknown: <why, citing file:line or what it depends on>
Fact: <the one fact the change is safe because of>: <file:line>   (or: none, a consumer breaks)
Proof: `<command>` passes on the change, fails with <the break>   (or: none: <why>)
Level: <1-5> (<what was done>)
```
