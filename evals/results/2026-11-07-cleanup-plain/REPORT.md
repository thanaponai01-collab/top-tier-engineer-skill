# cleanup-agent-leftovers: plain Opus baseline (2026-11-07)

Case: `evals/cases/cleanup-agent-leftovers`, a 26-file budget CLI written for the planned `cleanup`
skill (brief: `work/briefs/cleanup.md`). It plants 12 pieces of agent mess, 3 decoys that look like
mess but are used, and 3 things a cleanup should report: a swallowed error, a stub export, and a
January total hard-coded to pass its test. Only the plain arm was run, because the skill does not
exist yet. `python run.py --cases cleanup-agent-leftovers --arms without --repeats 3 --model opus --keep-workdirs`.

| try | grade | mess cleaned | decoys kept | nothing broken | cost | time | turns |
|---|---|---|---|---|---|---|---|
| 1 | PASS 5/5 | 12/12 | 3/3 | yes | $0.29 | 70 s | 10 |
| 2 | PASS 5/5 | 12/12 | 3/3 | yes | $0.24 | 54 s | 7 |
| 3 | PASS 5/5 | 12/12 | 3/3 | yes | $0.31 | 182 s | 10 |

Mean $0.28 a try. Every try reported the swallowed error, the stub and the hard-coded January, and
said why each decoy was kept (loaded by name, named in config.json, documented in the README).

## How plain Opus did it
It read every file, cleaned everything, ran each command before and after, and wrote a plain report.
Two tries in three also fixed the January bug instead of only reporting it: they took out the
special case, replaced `abs()` with a plain sum, and said in the report that this is the one change
in behavior. Tests stayed green because January's real total is the value that had been hard-coded.
Try 1 left the code as it was and added a comment pointing at the bug.

## What this means for the skill
On a small repo that fits in one read, plain Opus already cleans up perfectly. The skill cannot
improve this case. It can only add cost, as every earlier port showed on small apps (feature-map,
evolve-maintain, threat-model, perf-optimize, safe-release). If the skill helps, it will be where
reading everything in one pass is not possible, or where something has to carry over to a later
session:

1. **A repo too big to read in one pass.** Mess and decoys spread over a few hundred files, where
   finding every duplicate and every load by name needs a tool, not a read. (wire-check's
   `too-big-to-read` and feature-map's 133-command case are the precedent; plain Opus still passed
   wire-check's by writing its own AST script.)
2. **The record stage.** Two sessions: a cleanup, then a later agent adds new mess and brings back
   a deleted file, and a bare third session is asked what has changed since the cleanup. This is
   the only part of the brief that plain Opus has no reason to do unasked.
3. **A narrow follow-up.** A later session is asked to tidy one folder, while the mess that
   misleads is a parallel copy outside it (the "alarm on narrow task" kind, where feature-map won
   2/3 to 0/3).

One decision for the brief: in 2 tries out of 3, plain Opus fixed the test-gaming bug and said so
clearly. The brief's rule (report it only, never fix it) is stricter than what a good plain run
does. Either keep the rule, or allow the fix when the report names the change in behavior.

## With the skill (1.42.0, lean build)

The user is fine with plain Opus passing. The skill exists so the request does not have to be
explained every time, so it was built lean and judged on "no worse, no dearer".

| try | grade | mess cleaned | decoys kept | nothing broken | `CLEANUP: done` | cost | time | turns |
|---|---|---|---|---|---|---|---|---|
| 1 | PASS 5/5 | 12/12 | 3/3 | yes | yes | $0.25 | 56 s | 8 |
| 2 | PASS 5/5 | 12/12 | 3/3 | yes | yes | $0.25 | 52 s | 8 |
| 3 | PASS 5/5 | 12/12 | 3/3 | yes | yes | $0.24 | 48 s | 8 |

Mean $0.25 a try against $0.28 plain: a tie on quality at the same cost. Every try read SKILL.md,
ran the helper, cleaned, and reached `CLEANUP: done`, leaving `.cleanup/history.json` for the next
run to compare against. Plain runs leave no record (the scorecard's "skill not used" counts only
Skill-tool calls; these runs were pointed at SKILL.md and read it).
