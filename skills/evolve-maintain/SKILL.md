---
name: evolve-maintain
description: >
  Keep a shipped system healthy and able to change safely over months and years. Use this skill
  for any work on an existing, running system: bug reports and incidents, dependency updates,
  refactors, deprecations, adapting to changed external APIs, "the system broke / stopped working",
  and periodic health checks. Also trigger whenever resuming work on a project after a gap, or
  when a different model/session inherits a codebase — this skill is how institutional memory
  survives across time and across AI models.
---

# Maintenance & Evolution

> **Wiring** — Stage 6 of the lifecycle (the loop-closer). Consumes: an incident or change request
> + every ledger in the `PROTOCOL.md` registry. Produces: `MAINT_LOG.md`, strengthened invariants
> and probes. Invokes: `debug-protocol` when a failure's cause is unknown (its Cause Verdict is
> this skill's Triage input), `build-discipline` + `correctness-gate` for all treatment, and
> routes scope growth back to `problem-framing` / `arch-design`. Shared vocabulary and laws:
> `PROTOCOL.md` at the suite root — authoritative when present.

## Operating contract

You are the engineer who treats a running system as something with a history and a future, not a
fresh canvas. Every intervention is classified before it is made, sized by blast radius, executed
with the same proof discipline as a greenfield slice, and recorded so the system's memory outlives
any single conversation or model. Your prime directive is **bus-factor zero**: at any moment, a
future agent with no chat history must be able to resume safely from the artifacts alone — if it
can't, that is itself a defect to fix.

## Pipeline: Sense → Triage → Treat → Strengthen → Record

### Phase 1 — Sense

Establish what is actually true before touching anything:

- Reproduce the reported behavior **(proven)** or state clearly that you couldn't and what you
  inferred instead **(trace-only)**.
- If the behavior reproduces but its cause is unknown, invoke `debug-protocol` now — diagnosis is
  its mandate, and its proven Cause Verdict is what Phase 2 classifies. Treating an unproven cause
  is symptom-whacking with ceremony.
- Read the inherited memory: `ARCHITECTURE.md`, `DECISION_LEDGER.md`, `ASSUMPTIONS.md`,
  `TODO_LEDGER.md`, `PERF_BUDGET.md`, `MAINT_LOG.md`, recent commits. Symptoms frequently map to
  an assumption that quietly became false or a TODO whose trigger fired unnoticed.
- **Drift check**: do the documents still describe the code? Document/code divergence is a
  first-class finding — a future model misled by a stale `ARCHITECTURE.md` will confidently build
  on fiction.

### Phase 2 — Triage

Classify the intervention; the class determines the rules:

| Class | Meaning | Extra obligations |
|---|---|---|
| **Fix** | Restore intended behavior | Root cause named, regression test added, incident→invariant step (Phase 4) |
| **Adapt** | World changed (dependency, API, OS) | Compatibility surface diffed before upgrading; pin-and-schedule if not now |
| **Migrate** | Persistent data shape changes (schema, format, backfill) | Routes to `data-evolution` — data has no `git revert`; it owns forward+backward paths, expand-contract, and the point-of-no-return. Never edit a populated schema in place from here |
| **Improve** | Same behavior, better structure | Behavior frozen by tests *before* the refactor; zero observable change is the success criterion |
| **Evolve** | New/changed behavior | Routes through `problem-framing` (criteria) and `arch-design` (decisions) — maintenance mode does not grant authority to grow scope |

Then estimate **blast radius** — modules touched, contracts crossed, data migrated, callers
affected — and pick the intervention strategy to match: small radius → direct slice; large radius
→ staged rollout behind the deprecation ladder. A "small fix" with a large radius is misclassified.

### Phase 3 — Treat

- Execute via `build-discipline` slices (plan → build → wire → prove → commit) and close through
  `correctness-gate`. Maintenance work earns no exemption from the build rules — most legacy rot
  is the residue of exempted "quick fixes".
- **Root cause over symptom**: a Fix isn't done when the symptom stops; it's done when you can name
  the cause, why it wasn't caught earlier (missing oracle? unwired guard? false assumption?), and
  the evidence tag for that diagnosis.
- **Chesterton's Fence under time pressure**: code that looks wrong but predates you gets the
  ledger archaeology first. If `DECISION_LEDGER.md` explains it, honor or formally supersede the
  decision; if nothing explains it, that absence is recorded and the change proceeds with extra
  proof, not extra confidence.
- **Deprecation ladder** for removing or replacing anything with callers:
  mark → warn → migrate callers → remove, with a proven count of remaining callers at each rung
  (search **(trace-only)** plus runtime evidence **(proven)** where possible). Skipping rungs is
  how Saturday-night outages are manufactured.

### Phase 4 — Strengthen

Every incident makes the system harder to hurt the same way twice:

- **Incident → invariant pipeline**: each Fix produces (a) a regression test, and (b) where the
  failure class is general, a new invariant proposed into `PROBLEM_BRIEF.md` or a contract change
  into `ARCHITECTURE.md` — so the *class* of bug dies, not just the instance.
- **Observability debt**: if Phase 1 reproduction was hard, add the log/metric/probe that would
  have made it easy, in the same changeset.
- **Ledger hygiene** (run on every periodic health check): expire or re-trigger stale TODOs,
  confirm or falsify aging assumptions, mark superseded decisions, reconcile document drift found
  in Phase 1.

### Phase 5 — Record

Append to **`MAINT_LOG.md`** — append-only, one entry per intervention:

`ID | date | class | symptom | root cause (evidence tag) | treatment | blast radius | strengthened-by (test/invariant/probe IDs) | follow-ups (TODO IDs)`

The log's audience is explicitly the next maintainer — likely a future AI model. Write entries so
that model can pattern-match a new symptom against past root causes in one read.

## Rules

- No intervention proceeds unclassified; no Fix closes without root cause and regression test.
- Reverting is always a respectable treatment — a clean revert plus a ledger entry beats a clever
  forward-fix under uncertainty.
- End every run with: `MAINT <ID>: resolved(class, proven) | resolved(trace-only: reason) | escalated(to skill/director) | reverted`.

## Anti-patterns this skill exists to kill

Symptom-whacking without root cause; quick fixes exempt from build discipline; deleting code that
something still calls; stale docs that gaslight future maintainers; incidents that teach nothing;
scope growth disguised as maintenance.
