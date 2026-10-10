---
name: project-update
description: Maintain affected project memory after work; reconcile missed updates.
metadata:
  stage: build
  card: "keep project memory current after work"
---

# Project Update

Routine upkeep belongs to the working agent while it knows the task. Reconciliation is for missed
updates, conflicting records or several intervening sessions. Read the startup pointers, affected
records and the task's actual diff. Choose an explicit change range for reconciliation; HEAD alone
does not identify already committed work. If the range is unknown, report that limitation.

Follow [the memory convention](../project-context/references/memory.md). Without the helper,
update existing Markdown directly and check links/size by hand. Never require setup for a typo.
Reuse existing documents; create detail records only when their information outlives the task.

Update the observable result, unfinished work, blockers and one Next with a completion check.
Requirements change only when the owner changes them; preserve unresolved requirements even when
implementation differs. Verification definitions stay with VERIFY.md; actual receipts stay in
their evidence files. Link to them, do not copy logs. Record command, result and code baseline when
available; otherwise say unverified. Never upgrade a past pass to current proof without running
the relevant check. RUN.json retains execution authority; summaries must agree with it.

Update only affected feature/command/design entries. Keep current summaries small, split active
detail by area, and move completed history out of startup reading without losing unresolved work
or superseded decision links. Preserve existing archive eligibility rules. Changed source with no
mapped record is a coverage gap, not permission to call the memory complete.

When the helper is installed, run `context.py --repo <project> index --files <changed-context-paths>`
then `check --files <changed-context-paths>`. Include deleted context paths to remove their entries.
Full `index` is for setup/rebuild; full `check` is for reconciliation. Existing feature/check tools
still own semantic validation. Upkeep uses checks already performed; it does not rerun the suite.
An interrupted cache update can be rebuilt from files. Do not spawn a second agent for routine upkeep.

Report updated sources, evidence gaps and Next. No commits, pushes or releases are implied.

*Test:* a fresh reader finds the completed result and unfinished task without chat history; no check
is invented, owner intent survives, and a second unchanged upkeep produces no document edits.
