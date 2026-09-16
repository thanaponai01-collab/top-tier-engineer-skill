---
name: scrutinize
description: An outsider's second opinion on a change before it lands: PR, diff, plan or design doc. Use for "scrutinize this", "second opinion", "sanity-check this PR / plan".
---

# Scrutinize

Read the change cold. The author's confidence, the description and the polish count for nothing.
The diff is where you start, not where you stop.

*Evidence labels: **proven** = you ran it · **traced** = you read the whole chain, start to
end · **suspected** = neither.*

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

Run things wherever it's cheap.

## Report

Verdict first, **ship / fix-then-ship / rework / reject**, with the biggest reason. Then blocker →
major → minor: `file:line`, consequence, evidence (proven / traced / suspected), smallest fix. A clean
pass lists what you traced and ran; "LGTM" is not an answer. Drop nitpicks when there are real
problems.
