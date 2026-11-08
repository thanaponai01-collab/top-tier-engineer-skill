---
name: wire-check
description: >-
  Check that code is connected to the running system, not just written: run every real way in, see what it reaches, and name the first broken link for each piece nothing reaches. Use for "built but isn't working", "is this hooked up?", "what does nothing call?"
disable-model-invocation: true
metadata:
  stage: prove
  card: "built, but nothing happens"
---

# Wire Check

Say which code the running system really reaches and which it does not, and for each piece it does
not, the first link in the chain that is broken. A function counts as wired only when a real way in
reached it while it ran, not because something seems to import or name it. Report only, unless
asked to connect something. How you find the links is up to you: read it all if it fits, trace it,
run it.

**What done looks like**

- Every way in was run: each CLI command, the job runner or scheduler, each console script, each
  variant chosen by a name built at runtime, with the environment a deployment sets. A way in that
  cannot run here is named with the reason.
- Each piece nothing reached gets a verdict: not registered (nothing names it), not routed
  (registered, but no trigger maps to it), never invoked (a flag or branch nobody takes), effect lost
  (it runs, but its result or error is dropped), served (by a way in that cannot run here), or
  unknown (say what it depends on). Each verdict cites the `file:line` it rests on.
- A piece a real way in should reach is shown reached by running that way in, not given a verdict.
- When asked to connect something: the real trigger reaches it and does what it should, past every
  break in the chain, not just the first. A check stays in the project's suite that drives the real
  trigger and fails when the wiring is broken again, seen failing once with the wiring broken. If
  the repo has a `FEATURES.md` (feature-map) or a `VERIFY.md` (verify-loop), the feature's trace and
  check go there too.

**Avoid**

- Calling something an orphan because no file names it. Auto-discovery, decorators, plugins loaded
  from config or an env var, names built with f-strings, and a second entry point all wire code no
  grep finds. Wiring by hand what already registers itself is a bug, not a fix.
- Calling a piece wired because a test calls it directly. Only the trigger the users or jobs use
  counts.
- Deleting code that looks unused. Removing it is a cleanup decision for the user, not this skill.
- Stopping at the first broken link when connecting: an import fixed can still meet a wrong event
  name or a swallowed error behind it.

**The answer**

```
Ways in run: `<command>` (one per way in)      Not run: <way in>: <why>
Reached: <file::function or area>, by `<command>`   (one line per component in question)
Not reached:
- <file[::function]>: <not registered | not routed | never invoked | effect lost | served | unknown>
  — <the broken link, file:line>; <wire it as ..., or delete it, or what it depends on>
Connected: <component>: `<real trigger>` now reaches it; check `<test command>` fails with the
  wiring broken and passes now; FEATURES.md / VERIFY.md updated (or: not asked)
Not checked: <code, ways in or environments no run here reached>
```
