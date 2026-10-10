---
name: evolve-maintain
description: >-
  Change a running system without breaking it: upgrades, deprecations, removing an old API, large refactors. Use for "upgrade X", "refactor this module".
metadata:
  stage: build
  card: "upgrade, refactor or deprecate on a live system"
---

# Maintenance & Evolution

This skill decides **what kind of change this is and how far it reaches**; the change itself is
then built like new work. Nearly all maintenance damage is a misclassification — a "small fix" that
touched three contracts, an "upgrade" that was really a migration.

## 1. Sense
- Reproduce the reported behavior, or say plainly you couldn't and what you inferred instead.
- **Cause unknown → `debug-protocol` first, and come back with it proven.** Treating an unproven
  cause is symptom-patching, and it's how one bug gets shipped two fixes. No `debug-protocol`
  available here? Prove it yourself in both directions before treating anything: with the cause present
  the failure happens on demand, and with only the cause removed the same trigger stops
  failing.
- Read project notes and recent commits. Symptoms often trace to an assumption that quietly stopped
  being true, or a TODO whose moment came and went.
- **Drift check:** do the docs still describe the code? Stale docs are their own finding; the next
  reader will build on them.

*Test:* you reproduced it, or the report says what you inferred instead and on what basis.

## 2. Triage
| Class | Meaning | What it obliges |
|---|---|---|
| **Fix** | Restore intended behavior | Named cause, regression test, prevention (step 4) |
| **Adapt** | The world changed (dependency, API, OS) | Diff the compatibility surface *before* upgrading; pin and schedule it if not now |
| **Migrate** | Stored data changes shape | `safe-release` owns the forward and backward path; without it, nothing ships until the way back is written and tested |
| **Improve** | Same behavior, better structure | Freeze behavior with tests *before* refactoring; success is zero observable change |
| **Evolve** | New or changed behavior | Acceptance criteria first. Maintenance is not permission to grow scope |

For **Adapt** and **Improve**, run the existing suite before the first edit and keep the result: a
red run afterwards means something only if you know what was red before. Any action on a live
system (restart, config change, data fix) must fit the user's explicit environment, action and limits.
Use recorded upfront authority when it covers the move; ask only when absent or exceeded. Persist
intent and reconcile ambiguous external state before retrying.

Then size **how far it reaches**: modules, contracts, stored data, callers. Short reach → one direct
change. Long reach → staged, down the ladder below. A "small fix" that reaches far was
misclassified; go back to the table.

*Test:* the reach you named matches the class you chose. A "fix" that reaches contracts or stored data was misclassified — go back to the table.

Reusable proof: when VERIFY.md exists or reusable regression verification is requested, hand the
affected contracts and adjacent callers to `verify-loop`: load that skill, follow its
references/handoff.md and record the rejection and strict green through its bundled `verify.py`.
Direct output files are the fallback only when verify-loop is not installed. Do this before editing,
mapping the reproduced bug for Fix, compatibility cases for Adapt, preserved behavior for Improve. The check
baseline freezes expectations, not the implementation being refactored.

## 3. Treat
The change is `build-discipline`'s work, and that phrase is also the fallback if the skill
isn't loaded here: smallest slice, wired, proof line run, one revertable commit. Maintenance
adds three constraints:

- **Quick fixes get no exemption.** Most rot in old code is what earlier quick fixes left behind.
- **Code that looks wrong but predates you:** get the reason from git history first (`code-history`
  does this across every record; without it, `git log` and `git blame` on the lines). A reason you
  find is respected or explicitly replaced; no reason found means extra proof, not extra confidence.
- **Reverting is a legitimate fix** — better than a clever fix forward when you're unsure, and the
  one treatment that needs no diagnosis.

**Deprecation ladder**, for removing anything with callers: mark → warn → move the callers → remove,
counting remaining callers at each rung — a code search is traced, runtime evidence proven, prefer
it. Nothing comes off the last rung on a count of zero alone: proving a thing dead is
`latent-audit`'s job, and without it the three checks are yours — every textual reference
(strings, config, CI, templates, dynamic lookups), every caller outside this codebase, and a
run that shows it never loads.

*Evidence labels: **proven** = you ran it · **traced** = you read the whole chain, start to
end · **suspected** = neither.*

## 4. Strengthen

A fix that closes only this instance gets paid for again.
- Every Fix leaves a regression test named after the bug.
- Where the same *kind* of failure could happen elsewhere, raise it to an invariant or a contract
  change, so the class dies and not just the instance.
- If reproducing was hard, ship the log, metric or probe that would have made it easy, in the same
  change.
- On a periodic health check: close stale TODOs, confirm or drop old assumptions, fix doc drift.

*Test:* the regression test fails against the old code. One that passes either way guards nothing.

## 5. Record
Keep owner intent, affected documentation and the next step current using
[the context handoff](../project-setup/references/context-handoff.md). Run its structural check;
report unrelated pre-existing gaps rather than expanding a maintenance task to repair them.

If the project keeps a maintenance log, append:
`date | class | symptom | root cause | treatment | reach | guarded by | follow-ups`, written so a
future symptom can be matched to a past cause in one read.

## Report

The symptom in the reporter's words; the class and reach you triaged it as; the root cause in one
sentence, proven, traced or suspected; what now stops it coming back; what you left.

## Common mistakes

Treating a cause nobody proved; a migration triaged as a fix; scope growth wearing a maintenance
label; deleting code something still calls; closing a fix with no regression test; stale docs left
to mislead the next maintainer.

Project memory: retrieve missing facts with `project-context`; after authorized changes use
`project-update` for affected records. Without helpers, follow/update existing notes directly;
read-only reviews report gaps. Skip upkeep when no durable fact changed.
