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

**Goal:** the next agent can work here without being misled. Remove what is redundant or left
behind, keep everything that is used working, and tell the user in plain words what you removed,
what you kept that looked like mess, and what you found but did not change. You clean the mess;
restructuring (splitting files, moving modules) is untangle's job, so name it and leave it.
`C` is `python <this skill's base directory>/scripts/cleanup.py <repo>`, run from the repo root.

1. `C [paths] --run "<test cmd>"` before you change anything. It lists candidates in
   `.cleanup/candidates.md` and records the files and the tests. With a record from an earlier
   cleanup it lists what is new since then and what came back after being deleted; put that first in
   the answer. No tests? Say so, and record a command that runs the app instead.
2. Read the code and clean. Candidates are leads, not verdicts: the helper misses copies that are
   not exact (two config readers written differently) and flags things that are used. Before you
   delete, look for loads by name: `import_module` or `require` with a built string, names in config
   files, scripts the README tells people to run, entry points. Merge duplicates into the copy most
   callers use. Run what you touched.
3. `C --done`. It reruns the recorded tests and refuses while a test that passed now fails, fewer
   tests run, or a deleted file's name is still written somewhere. Fix the cause, never the check.
   It saves `.cleanup/history.json` and prints `CLEANUP: done`.

Swallowed errors, stubs and hard-coded answers change behavior when fixed. Name each one. Fix it
only when it is clearly a bug, and then say in the answer that this changes what the program does.

The answer, in plain words: what came back since last time (if a record exists), removed, merged,
kept though it looked like mess (and why), found but not changed. Leave `.cleanup/` in place: the
next run compares against it.
