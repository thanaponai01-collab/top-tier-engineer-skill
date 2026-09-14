---
name: ship-gate
description: >
  Decide whether a verified change is safe to release, and guarantee it can be reversed. Use at deploy/release/merge-to-main time — "deploy", "release", "ship it", "push to prod", "cut a version" — after correctness-gate clears.
---

# Ship Gate

> **The question:** Can this release be undone, watched, and kept small?  ·  Inputs, outputs and who runs next: `PROTOCOL.md` §4.

## When not to use this

"is it correct" → `correctness-gate`; "is it secure" → `threat-model`; "is it wise" → `senior-review`; changing persistent data shape → `data-evolution` (ship-gate gates the deploy that carries the migration, data-evolution owns the migration itself).

You treat deploying as the highest-stakes one-way door there is, and refuse to walk through it
without a proven way back. Correct code that cannot be rolled back, that ships with nothing
watching it, or that updates every user at once is not ready. Ready means *released and
reversible*, not *passing*. A green gate gets you to this door; it does not open it.

## The job

1. **No release without a rollback you have proven.** "We can revert the commit" is
   **(trace-only)** until someone actually shows the revert working — and it is often untrue (a
   migration ran, a cache filled, a message went out). Write the rollback procedure, and either
   test that it works or tag it honestly. A release that cannot be undone is the director's
   decision (a one-way door, meta-skills Discipline 3), never the default.
2. **Limit how far it reaches before release, not after.** Roll out in stages (a canary, then a
   percentage, then everyone, or behind a feature flag) rather than to everyone at once. A change
   that can only go to 100% of users at once has to say so, and that alone makes it a director's
   go/no-go.
3. **Ship watching, not hoping.** Before release, name the one to three signals that will show this
   change working or failing in production (error rate, latency, the specific number this change
   affects) and confirm they already exist. If they don't, the release is blind — send that to
   `evolve-maintain` as missing visibility, and the gate says whether it ships blind anyway or
   waits.
4. **The release is responsible for everything it carries.** Config changes, migrations, new
   secrets, dependency upgrades, and unused feature flags all come along with it. List each one; a
   migration goes to `data-evolution` for its own plan to undo it, and that plan becomes this
   gate's evidence.
5. Law 4 and Law 5 apply: the go/no-go is a plain-language call the director can make themselves,
   and the rollback procedure ships as steps you can run, not a description of steps.

## Steps: Precondition → Reversibility → Blast radius → Observability → Go/No-go → Record

### Phase 1 — Precondition
Confirm the upstream gates: `correctness-gate` pass, and where a trust boundary is touched, a
`threat-model` clear. A missing upstream gate is not waived here — it is run first or the release
blocks. State each gate's verdict line as inherited evidence.

### Phase 2 — Reversibility
Write the rollback procedure as concrete steps and classify the release:
- **Reversible** — revert restores the prior working state; demonstrate it where the environment
  allows **(proven)**, else **(trace-only)** with the command that would prove it.
- **Reversible-with-data** — a migration ran; rollback requires `data-evolution`'s down-path. Hand
  off; its plan is attached here.
- **Irreversible** — emails sent, cards charged, data deleted, a public contract published. Take it
  to the director as a one-way door, with the cost of being wrong; never proceed on your own.

### Phase 3 — Blast radius
State who is affected and how that is limited: a canary, a percentage, a flag, or "everyone at
once" said out loud. Match the rollout to how reversible it is — anything irreversible gets the
most cautious staging the system supports.

### Phase 4 — Observability
Name the signals that confirm health post-release and the threshold that triggers rollback. Confirm
each signal exists and is watched. Missing signals → `evolve-maintain` (add the probe) and a stated
choice: wait for it, or ship blind and say so.
- **Can anyone tell *why* it fired?** (DECISION_LEDGER D001) A named signal is not enough if,
  when it goes off, nobody can tell what caused it. For each signal, confirm the rollback trigger
  can actually be followed end to end: the metric exists, it is specific to this change rather than
  buried inside a total, and whoever is on call can get from "the signal fired" to "this release
  caused it" without adding new instrumentation. A signal that fires but cannot point at a cause is
  the same as no signal; send that gap to `evolve-maintain` before go/no-go, exactly like a missing
  one.

### Phase 5 — Go/No-go
Give the director the call in plain language: ship, stage, or hold; the single biggest risk; the
rollback trigger; and, if this is a one-way door, exactly what they are approving. At most three
options, one recommendation, and the cost of being wrong (meta-skills Discipline 3).

### Phase 6 — Record
Record the release plan — inline, or as a file when §3 warrants one: precondition verdicts,
reversibility class + rollback steps, rollout
strategy, watch signals + rollback trigger, and the go/no-go decision with its date. After release,
incidents route to `evolve-maintain`, which reads this file to know what was expected.

## Report

Shape and wording: `PROTOCOL.md` §9. The rows are the blockers, one each. The release plan, the
rollback steps and the watch signals go under `Detail`.

a `SHIP` line (PROTOCOL §5) — a go is `done(<strategy>, rollback <tag>)`, a hold is `findings(<blocker>)`, and an undecidable one-way door is `blocked(one-way door: …)`.

## Common mistakes

Treating a green correctness gate as permission to deploy; "we'll just revert" with no revert
anyone has tested; rolling out to everyone at once a change that is only reversible in theory;
shipping with no health signal to watch; migrations that come along unplanned; walking through an
irreversible release without asking the director.
