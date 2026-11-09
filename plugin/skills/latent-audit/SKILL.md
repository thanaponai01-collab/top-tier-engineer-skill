---
name: latent-audit
description: >-
  Find dead code and remove it without breaking anything: only code that is truly never loaded or called goes, every command is rerun after, and every file that looked dead gets a verdict. Also checks a declared layer order. Use for "find dead code", "clean up the codebase", "are the layers respected?"
disable-model-invocation: true
metadata:
  stage: review
  card: "dead code and layer violations"
---

# Latent Audit

Remove the code nothing reaches, keep everything that is reached, and account for every file or
function that looked dead. "No import names it" is a suspicion, not proof: code is also loaded by
a name built at runtime (`import_module(f"...{fmt}_report")`, `require` of a built string), by a
name written in a config file or schedule, through plugins and entry points, by a script the README
tells people to run, or from outside the language altogether. A green test suite proves nothing
about code the tests never touch. How you find what really reaches the code is up to you. If
`FEATURES.md` (feature-map) or `VERIFY.md` (verify-loop) is in the repo, its recorded ways in and
checks count among the commands that could notice a deletion. `scripts/graph-audit.py <repo>` is
there if it helps. It prints the import graph and the suspects, and `--snapshot --run "<cmd>"`
records what each command really imports. You don't have to use it. Report only, unless the user
asked you to delete.

**What done looks like**

- Before anything changes, every command that could load the code (the app's commands, jobs, the
  tests, the recorded checks) was run and passed, so there is something to compare with.
- Only code shown to be never loaded or called is deleted, in place. After deleting, every one of
  those commands runs again and still does what it did before.
- Every suspect gets a verdict: `dead` (deleted, or reported if deletion wasn't asked for), `live`
  (with the `file:line` that loads it), or `watch` (kept, with what would settle it).
- A deleted file's name is spelled nowhere that would still try to load it.
- If the repo declares a layer order, every import that points up it is listed by `file:line`.
  With no declared order, the layers are "unchecked", never "clean".
- The verdicts stay in `.latent/verdicts.md`, so a later session asked to delete something can
  see what was already shown live and why.

**Avoid**

- Deleting on a grep, a static graph, green tests, or someone's word that it is dead.
- Changing code that is not dead: no refactors, renames or "while I'm here" fixes.
- Calling a command green that wasn't run after the last deletion.

**The answer**

```
Deleted: <file or function> (<why nothing reaches it>)          (one line each, or: none)
Kept though it looked dead: <file>: live via <file:line that loads it>
Watch: <file>: <why it is kept, what would settle it>
Layers: <file:line> imports up from <layer> to <layer>          (or: none, or: unchecked, no declared order)
Commands: `<command>`: passed before, passed after              (one line each)
Record: .latent/verdicts.md
```
