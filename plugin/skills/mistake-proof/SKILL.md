---
name: mistake-proof
description: >-
  Make a mistake agents keep repeating in this repo impossible, with a check proven to fail on a real past mistake. Use for "agents keep doing X", "stop this happening again", "/correct", or after the operator corrects you.
disable-model-invocation: true
metadata:
  stage: review
  card: "agents keep making the same mistake"
---

# Mistake Proof

**Goal:** every mistake that happened twice is a class with its evidence, fixed at the strongest
level that works, and held by a check that ran red on the commit where the mistake is and green on
the working tree. A line in CLAUDE.md that nothing enforces is not a fix. How you find the
mistakes and write the checks is yours. What counts as done is checked by the helper.
`M` is `python <this skill's base directory>/scripts/mistake.py <repo>`.

`M --mine [--since <ref>]` lists candidates in `.mistakes/candidates.md`: reverts, later commits
that bring a reverted change back, fixes that name an earlier commit, and workaround comments
(`# don't`, `# must`, `NOTE:`). When the operator corrects you, `M --add "<what they corrected>"`
records it, dated, as evidence `added:N`. Group the repeats in `.mistakes/classes.md` (the header
shows the format). Run `M --gate` whenever you like; it says which stage is open and what fixes
it, drafts the reply once stages 1 and 2 hold, and ends `MISTAKE-GATE: done`.

Assume the next contributor is an agent that sees only the files it opened, copies the nearest
example, and takes the shortest path that compiles. Fix so a change that looks right from one
file is right for the whole repo. Levels, strongest first:

1. **architecture**: one owner per piece of state, one supported way, the wrong import fails, old
   ways deleted (one with live callers: use evolve-maintain)
2. **types**: the bad state cannot be written
3. **a lint or CI check** whose error names the file, type or function to use instead
4. **a test** of behaviour
5. **docs only**, for judgment calls. Nothing fails when it is skipped, so it stays `unenforced`

## The stages

| Stage | Holds when |
|---|---|
| **1. Classes** | Each `## <class>` has two or more `- evidence:` lines that exist: a commit sha, a `file:line`, or `added:N` |
| **2. Level** | `- level: N`, and a `- why not K:` line for every stronger level K, saying why it did not work |
| **3. Proof** | Levels 1-4: `` - check: `<cmd>` `` exits non-zero on `- mistake: <sha>` (the commit with the mistake; `- check-files:` are copied onto it) and zero on a copy of the working tree. Old uses already common? Fail only on lines a change adds. With CI config in the repo, the same command runs there |
| **4. Rules** | The agent file (CLAUDE.md, AGENTS.md or `.cursor/rules/`) has a table between `<!-- mistake-rules -->` and `<!-- /mistake-rules -->`: `\| class \| rule \| level \| enforcer \| added \|`, one row per class (the gate drafts it). The enforcer is the check's file or its command in backticks, `none` at level 5. A level-5 class with evidence newer than its row is a repeat: fix it at level 1-4 in the same change. Each `mistake-ok: <class> reason=... expires=YYYY-MM-DD approved=<name>` exception has all three, a date to come, and a human's name you never fill |

Fix the most frequent classes first, one commit each. Drop a row once its mistake cannot happen.

Fill the slots of `.mistakes/answer.md`, then `M --answer-check .mistakes/answer.md`: it refuses a
class the gate did not clear, a status other than the one recorded (a level-5 class called
enforced), a cleared class left out, and unfilled slots. Give that answer: each class with its
evidence, its level, and why a stronger level did not work.

The helper never writes the product tree: checks run in throwaway copies, and only `.mistakes/`
changes. Your fixes are ordinary edits. Commit `.mistakes/` with them.
