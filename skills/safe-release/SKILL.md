---
name: safe-release
description: >
  Release a change, or change the shape of stored data, with a proven way back. Use at deploy time ("deploy", "release", "ship it", "push to prod", "cut a version") and for data changes ("migration", "alter table", "change the schema", "backfill", "rename this column").
---

# Safe Release

Deploying is the highest-stakes one-way door there is. Ready means *released and reversible*, not
*tests passing*. And data is the one thing a revert can't bring back: a dropped column doesn't
return, and `git revert` doesn't un-corrupt a bad backfill.

## Rules

1. **No release without a rollback you've shown works.** "We can revert" is a guess until tested,
   and often false (a migration ran, a cache filled, an email went out). Write the rollback steps
   and test them, or say plainly they're untested.
2. **Limit reach before release.** Canary, percentage, or feature flag rather than everyone at once.
   If it can only go to 100% at once, say so; that makes it the owner's call.
3. **Ship watching, not hoping.** Name 1–3 signals that will show this change working or failing
   (error rate, latency, the specific number it affects) and confirm they exist. Each must point at
   *this* change, not a total it's buried in. Missing signals: add them first, or ship blind and
   say so.
4. **The release owns everything it carries:** config changes, migrations, new secrets, dependency
   upgrades, feature flags. List each.
5. **Irreversible actions go to the owner.** Emails sent, cards charged, data deleted, a public API
   published: present the cost of being wrong and wait for a decision.

## Releasing code

1. **Precondition.** Tests pass. Where a trust boundary changed, security was checked. Missing →
   do it first.
2. **Reversibility.** Write concrete rollback steps and classify: *reversible* (revert restores the
   prior state; demonstrate it if possible), *reversible with data* (needs the migration's backward
   path below), or *irreversible* (Rule 5).
3. **Blast radius.** Who's affected and how that's limited. The less reversible, the more cautious
   the rollout.
4. **Watch.** Signals and the threshold that triggers rollback (Rule 3).
5. **Go / no-go.** In plain language: ship, stage, or hold; the biggest risk; the rollback trigger;
   and for a one-way door, exactly what's being approved.

## Changing stored data

1. **Inventory.** Current shape, row count, constraints, foreign keys, and **every caller that reads
   or writes this data**. A missed caller breaks mid-deploy.
2. **Design both directions.** Forward (old → new) and backward (new → old). Name the **point of no
   return** (after which rollback loses data) and exactly what's lost. No lossless way back → Rule 5.
3. **Expand.** Add the new structure alongside the old. Old code keeps working. Deploy this alone;
   it's always reversible.
4. **Backfill.** Copy or transform old → new in batches, safe to re-run. Write to both shapes during
   the transition so nothing new is missed. One unbatched backfill on a big table is an outage.
5. **Verify on a copy first.** Row counts match, constraints hold, no forbidden nulls, and **read a
   sample of real transformed records**. "It ran without error" is not "the data is right".
6. **Contract.** Switch reads to the new shape and watch. Remove the old structure in a *later*,
   separate deploy, never the same one as the read switch. This is the point of no return.

Never a single `ALTER` that both adds and removes on a live system. Adding an index to a populated
table: use the engine's non-locking method.

## Report

Open with the call (ship / stage / hold), the biggest risk, and whether any rollback loses data and
at which step. Then one row per blocker, or per migration step: step, forward action, backward
action, lossy from here? Then runnable rollback steps, migration and rollback code, watch signals,
and verification evidence.

## Common mistakes

Treating green tests as permission to deploy; "we'll just revert" with no tested revert; everyone at
once for a change that's only reversible in theory; no health signal; migrations riding along
unplanned; destructive one-step migrations; backfills nobody checked; dropping the old column in
the same deploy that switches reads.
