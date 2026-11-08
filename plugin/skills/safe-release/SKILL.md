---
name: safe-release
description: >-
  Deploy, or change stored data, with a way back that was run, not guessed. Use for "deploy", "ship it", "push to prod", "migration", "alter table", "backfill".
disable-model-invocation: true
metadata:
  stage: ship
  card: "deploy, or change the shape of stored data"
---

# Safe Release

Say whether the release can go out (ship, stage or hold), and give a way back that was run, not
guessed. Data is the one thing a revert cannot bring back, so every loss is named with the step that
causes it. The live data is never written: everything is rehearsed on copies, and running the
release is its owner's call. How you read the change and choose its shape is up to you.

**What done looks like**

- The change and its way back ran on a copy of the live data, not an empty test database: forward,
  forward again (a rerun after a half-failed deploy must be safe), then back, with the data after
  back compared row for row with the data before.
- Today's code was run on the migrated copy. It keeps running there between the migration and the
  restart, and again after a code-only revert. If it breaks there, the shape changes (add and copy
  first, switch reads, drop in a later release) or the answer says how no old code ever runs on
  the new data.
- The checks use the data through the code the way the product does, including a write: a sign-up,
  an order, a job's run, not just a SELECT. Each passes on today's code and today's data first.
- Every constraint the change drops (a UNIQUE, a NOT NULL, a foreign key) is kept or named with why
  losing it is fine. A new required column with no default breaks every insert written before it.
- The live data is byte-for-byte as it was when the work started.
- Make the change only when asked; otherwise rehearse what is there and report.

**Avoid**

- Trusting a written rollback. "Revert the commit" or "redeploy the last tag" leaves the data as
  the migration made it; a down step nobody ran is a guess.
- A green suite that only ever builds a fresh database. It cannot see the rows the change mangles
  (a cast that truncates, an empty total, the only copy of a value in a column being dropped).
- Running anything against the live data, or any outward action (an email, a charge, a deletion,
  a public API call) without the owner's explicit yes for that action.
- Leaving scratch copies behind. Delete them, or commit the rehearsal with the change.

**The answer**

```
Call: ship | stage | hold — <one line why>
Change: <what it does to the data, in the shape it ships in>
Rehearsed on a copy of <live data>: forward <ok/fail>, again <ok/fail>, back <ok/fail>;
  after back: <same row for row / differs: what>
Today's code on the migrated data: <passes / breaks: what> (or: never runs there because <how>)
Rollback: <the rehearsed steps, in order>
Losses: <what is lost>: after <step>        (one per loss; or: none, back restores every row)
Dropped: <constraint>: <kept / why losing it is fine>    (or: none)
No return: <the step after which going back loses data>  (or: none)
Watch: <1-3 signals that point at this change, and the level that triggers the rollback>
Live data: untouched (checked <how>)
Not rehearsed: <data, services, jobs or code paths no run here reached>
```
