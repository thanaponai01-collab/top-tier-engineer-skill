---
name: scrutinize
description: >-
  An outsider's second opinion on a PR, diff, plan or design doc before it lands. Use for "second opinion", "sanity-check this PR".
disable-model-invocation: true
metadata:
  stage: review
  card: "second opinion on a PR, diff or plan"
---

# Scrutinize

Read the change cold. The author's confidence, the description and the polish count for nothing.
The diff is where you start, not where you stop.

*Evidence labels: **proven** = you ran it · **traced** = you read the whole chain, start to
end · **suspected** = neither.*

## 0. Get the change

Name what you are reading and how you got it: `gh pr diff <n>`, `git diff <base>...HEAD` (say which
base), or the path of the plan. Say it first in the report; a review of the wrong diff is a real
answer to nobody's question.

## 1. Should it exist?

State the goal in one sentence. Can't? It's underspecified: say what's missing and stop. Then look
for less: is the problem real, does something here already do this, is there a change with 90% of
the value at 10% of the risk, could it be config instead of code? A better alternative leads the
report. Skip this only if told not to question scope, and say you skipped it.

*Test:* you can state the goal in one sentence and name the cheaper alternative you weighed against it.

## 2. Trace the real path

For each claimed behavior: entry → call sites → branches → state changed → effect, including the
unchanged code around the diff. For a plan, trace it against the existing system. Note every
surprise; that's where the bugs are.

*Test:* you can name something outside the diff that the diff changes.

## 3. Attack

- **Claim vs confirmed:** "Claims X. Path A → B → C. At C, [what you saw]. Holds / doesn't."
- **Breaking inputs:** empty, huge, unicode, concurrent, retried, failing halfway.
- **Silent changes:** performance, error meaning, logs, stored formats, contracts other callers use.
- **The tests:** do they run the path you traced, or mock around it?

## 4. Test the decisive assumption

Name the one or two assumptions that make the change safe: for example, a persisted format stays
compatible, a schema field remains available through the migration window, shutdown happens only
after consumers stop, a pinned library preserves an error contract, or a flag has the same meaning
at every entry point. Trace that assumption through relevant configuration, schemas, lifecycle
ordering, pinned dependencies and indirect consumers beyond direct callers. Do not turn this into a
full impact map: stop when the decisive boundary is identified, and mark any uninspected path
**unknown**.

Use an unchanged consumer or boundary fixture where one is available. Run the smallest probe that
would fail on the bad behavior and pass on the safe behavior; retain the command and result. A
source read is **traced**, not **proven**. If the fixture cannot exercise both behaviors, report
that limit instead of calling the assumption verified.

*Test:* name the safety assumption, the unchanged boundary that depends on it, and the bad/safe
probe result (or the specific unknown that prevents one).

Run things wherever it's cheap, from a scratch checkout, and not code from an author you have no
reason to trust. Make the scratch checkout with `git worktree add <temp dir> <branch>` and remove
it afterwards (`git worktree remove <temp dir>`); never switch the person's own checkout to another branch. Post nothing on the PR or ticket unless asked.

## Report

Verdict first, **ship / fix-then-ship / rework / reject**, with the biggest reason. Then blocker →
major → minor: `file:line`, consequence, evidence (proven / traced / suspected), smallest fix. A clean
pass lists what you traced and ran; "LGTM" is not an answer. Drop nitpicks when there are real
problems.
