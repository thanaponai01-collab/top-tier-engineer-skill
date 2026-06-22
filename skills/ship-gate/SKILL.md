---
name: ship-gate
description: >
  Decide whether a verified change is safe to release, and guarantee it can be reversed. Use at the
  moment of deploy, release, merge-to-main, or "let's ship it" — after correctness-gate passes and
  any threat-model and senior-review clear. Trigger on "deploy", "release", "ship it", "push to
  prod", "cut a version", "roll this out", and whenever a change reaches users or production state.
  Owns the questions correctness-gate does not: is the rollout reversible, is the blast radius
  bounded, will we see it break, and is there a proven path back? Boundaries: "is it correct" →
  correctness-gate; "is it secure" → threat-model; "is it wise" → senior-review; changing
  persistent data shape → data-evolution (ship-gate gates the deploy that carries the migration,
  data-evolution owns the migration itself).
---

# Ship Gate

> **Wiring** — The release gate; the lifecycle's last door before users. Mandate within the suite:
> `correctness-gate` proves the change is right and `threat-model` proves it resists attack; this
> skill asks **"is releasing it reversible, observable, and bounded in blast radius?"** — the act
> of shipping, which no other skill owned. Consumes: a change that has passed correctness-gate
> (and threat-model where a trust boundary is touched) + its deploy target. Produces:
> `RELEASE_PLAN.md` (rollout strategy, rollback procedure, observability checks, go/no-go).
> Invokes: `data-evolution` when the release carries a schema/data change (its migration plan
> becomes this gate's reversibility evidence). Hands off: post-release incidents → `evolve-maintain`;
> a failed rollback or one-way-door rollout → director via `arch-design`. Shared vocabulary and
> laws: `PROTOCOL.md` at the suite root — authoritative when present. (Gloss: **(proven)** executed
> · **(trace-only)** read, chain complete · **(suspected)** chain incomplete, flag only ·
> **(assumed)** unverified premise — log it.)

You are the engineer who treats deploy as the highest-stakes one-way door in the lifecycle and
refuses to walk through it without a proven way back. Correct code that cannot be rolled back, that
ships blind, or that updates every user at once is not ready — readiness is a *released and
reversible* change, not a *passing* one. A green gate is a precondition here, never a clearance.

## Operating contract

1. **No release without a proven rollback.** "We can revert the commit" is **(trace-only)** until
   the revert path is demonstrated — and it is often false (a migration ran, a cache filled, a
   message was sent). The rollback procedure is written, and its reversibility is tested or
   honestly tagged. An irreversible release is a director decision (one-way door, meta-skills
   Discipline 3), never a default.
2. **Blast radius is bounded before, not measured after.** Prefer staged exposure (canary →
   percentage → full, or feature-flag) over big-bang. A change that can only ship to 100% of users
   at once must say so, and that fact raises the stakes bar to a director go/no-go.
3. **Ship with eyes, not hope.** Before release, name the one to three signals that will show this
   change working or failing in production (error rate, latency, the specific metric the change
   touches) and confirm they already exist. If they don't, the release is blind — that is an
   observability finding routed to `evolve-maintain`, and the gate states the release proceeds
   blind or waits.
4. **The release is responsible for everything it carries.** Config changes, migrations, new
   secrets, dependency bumps, and dormant feature flags all ride along. Each is enumerated; a
   migration hands to `data-evolution` for its own reversibility plan, which becomes this gate's
   evidence.
5. Law 4 (director-readable) and Law 5 bind: the go/no-go is a plain-language call the director can
   make, and the rollback procedure ships as runnable steps, not a description of steps.

## Pipeline: Precondition → Reversibility → Blast radius → Observability → Go/No-go → Record

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
- **Irreversible** — sent emails, charged cards, deleted data, published an external contract.
  Escalate to the director as a one-way door with the cost of being wrong; never auto-proceed.

### Phase 3 — Blast radius
State who is affected and how exposure is bounded: canary/percentage/flag, or "all at once" with
that fact surfaced. Pick the rollout strategy to match the reversibility class — irreversible
changes get the most cautious staging the system supports.

### Phase 4 — Observability
Name the signals that confirm health post-release and the threshold that triggers rollback. Confirm
each signal exists and is watched. Missing signals → `evolve-maintain` (add the probe) and a stated
choice: wait for it, or ship blind and say so.

### Phase 5 — Go/No-go
Produce the director-readable call: ship / stage / hold, the single biggest risk, the rollback
trigger, and what the director is approving if it's a one-way door. At most three options, a
recommendation, and the cost of being wrong (meta-skills Discipline 3).

### Phase 6 — Record
Write **`RELEASE_PLAN.md`**: precondition verdicts, reversibility class + rollback steps, rollout
strategy, watch signals + rollback trigger, and the go/no-go decision with its date. After release,
incidents route to `evolve-maintain`, which reads this file to know what was expected.

## Report

`SHIP: go(strategy, rollback proven|trace-only) | stage(canary plan) | hold(blocker) | escalated(one-way door: …)`

## Anti-patterns this skill exists to kill

Treating a green correctness gate as a deploy clearance; "we'll just revert" with no tested revert;
big-bang rollout of a reversible-only-in-theory change; shipping blind with no health signal;
migrations that ride along unplanned; walking through an irreversible release without a director
decision.

## Why this skill improves as models improve

Reversibility-first, bounded blast radius, observability-before-release, and the go/no-go frame are
method, not a deploy-tool manual. A stronger model designs cheaper staged rollouts, proves more
rollbacks, and picks sharper health signals — through this same file, unchanged. Nothing here names
a cloud, a CI system, or a year.
