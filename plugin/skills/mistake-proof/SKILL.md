---
name: mistake-proof
description: >-
  Make a mistake agents keep repeating in this repo impossible, held by a check that fails on a real past mistake. Use for "agents keep doing X", "stop this happening again", "/correct", or after the operator corrects you.
disable-model-invocation: true
metadata:
  stage: review
  card: "agents keep making the same mistake"
---

# Mistake Proof

Agents in a repo keep making the same mistakes, and the usual fix is one more line in CLAUDE.md
that the next agent never reads; nothing fails when it is skipped. Find the mistakes that keep
coming back and make each one impossible, or at least loud: a check that fails when the mistake
is made again. Assume the next contributor is an agent that sees only the files it opened, copies
the nearest example and takes the shortest path that compiles, so fix it so a change that looks
right from one file is right for the whole repo. How you find the mistakes and write the fixes is
up to you.

**What done looks like**

- The mistakes are found in the repo itself, not guessed: reverts, later commits that bring a
  reverted change back, fixes that name an earlier commit, workaround comments (`# don't`,
  `# must`, `NOTE:`) next to code, and the operator's corrections in this session.
- Each mistake class has at least two real pieces of evidence (a commit sha or `file:line` that
  exists, or a correction quoted with its date). One occurrence is a bug for debug-protocol, not a
  class.
- Each class is fixed at the strongest level that works, and says why each stronger one did not:
  1 architecture (one owner per piece of state, one supported way, the wrong import fails, the old
  ways deleted), 2 types (the bad state cannot be written), 3 a lint or CI check whose error names
  the file, type or function to use instead, 4 a test of behaviour, 5 docs only, for judgment calls.
  Deleting an old way that still has live callers is a migration: use evolve-maintain if it is
  installed.
- Every class at levels 1-4 has a check that was run failing on the commit with the mistake and
  passing on the working tree. If the bad pattern is already common, the check fails only on lines
  a change adds. If the repo has CI, the check runs there.
- The agent file (CLAUDE.md, AGENTS.md or `.cursor/rules/`) has one rule per class naming what
  enforces it: the check's file or command, or `none` at level 5. A level-5 rule whose mistake
  happened again after it was written is a repeat, and gets fixed at level 1-4 now.
- The most frequent classes are fixed first, one commit each.

**Avoid**

- A rule in prose that nothing enforces, called a fix. It stays `unenforced` in the answer.
- A check that passes on the past mistake too: it cannot fail, so it proves nothing.
- A check that fails on every old use, so the first person who hits it switches it off.
- Granting exceptions yourself. An allowed exception names its reason, an expiry date and the
  human who approved it; leave that name for the human to write.

**The answer**

```
Classes: <n> found, <n> fixed, <n> unenforced
<class>: level <1-5>: <rule>
  Evidence: <sha | file:line | correction, date>             (two or more)
  Why not stronger: <level>: <why it did not work>             (one per stronger level)
  Check: `<command>` fails on <sha>, passes now; CI: yes | no | no CI   (or: none, level 5)
  Enforcer: <file or `command`> in <agent file>                (or: none, unenforced)
Repeats: <class whose docs-only rule was broken again, with the evidence>   (or: none)
Not checked: <what history or corrections were not looked at>
```
