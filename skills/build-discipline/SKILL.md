---
name: build-discipline
description: >
  Execute a build in small, provable, fully-wired increments. Use this skill whenever writing or
  generating code for a feature, tool, or system — greenfield or addition — especially in Claude
  Code or any agentic build session. Trigger on phrases like "build it", "implement this",
  "add the feature", "make it work", or whenever code is about to be written against an existing
  PROBLEM_BRIEF.md or ARCHITECTURE.md. Also trigger when a previous build session left work
  half-finished and needs to be resumed safely.
---

# Build Discipline

> **Wiring** — Stage 3 of the lifecycle. Consumes: `ARCHITECTURE.md` + `PROBLEM_BRIEF.md` (invoke
> their producers if absent, or log the gap per `chief-engineer` Rule 2). Produces: proven slices
> as rollback-ready commits, `TODO_LEDGER.md`. Invokes: `wire-check` as the exit gate of every
> slice (Phase 3). Downstream: `correctness-gate`. Shared vocabulary and laws: `PROTOCOL.md` at
> the suite root — authoritative when present.

## Operating contract

You are the builder who never produces orphan code. Work advances in **vertical slices** — each
slice is the smallest increment that can be proven working end-to-end — and a slice is not done
until it is wired, exercised, and committed in a state the system could ship from. You build
against `ARCHITECTURE.md` and `PROBLEM_BRIEF.md`; departures from either are surfaced, never
smuggled in. Every "it works" claim carries **(proven)** or **(trace-only)** per `PROTOCOL.md` —
and inside this skill, only **(proven)** closes a slice.

## Pipeline per slice: Plan → Build → Wire → Prove → Commit

### Phase 1 — Plan the slice

- Pick the smallest unit of work that produces an observable behavior change reachable from the
  system's real entry point. "Half a backend with no caller" is not a slice; "one endpoint, wired,
  returning real data for one case" is.
- State the slice's **proof line** before writing code: the exact command, request, or interaction
  that will demonstrate it works, and what output counts as success. If you can't state the proof
  line, the slice is too vague to build.
- Check `ASSUMPTIONS.md` and the decision ledger for anything this slice touches. Building on an
  open assumption is allowed; building on one without noticing is not.

### Phase 2 — Build

- **Smallest diff that satisfies the proof line** (meta-skills Discipline 7, simplicity): prefer
  deleting or reusing over adding; introduce an abstraction on its second concrete use, not its
  first guess; "might need it later" is a `TODO_LEDGER.md` entry with a trigger, never speculative
  structure in the code.
- **Interfaces from ground truth, not memory**: verify an external dependency's interface against
  this environment's ground truth before coding against it (cutoff rule, PROTOCOL §1) — a
  remembered API is **(assumed)**.
- **Error paths first**: write what happens on bad input, missing dependency, and partial failure
  before polishing the happy path. Happy-path-only code is the largest single source of later
  incidents.
- **Names carry the documentation load**: a function whose name and signature don't explain it gets
  renamed before it gets commented.
- New conventions are forbidden mid-slice. If the architecture's conventions don't cover a case,
  stop, propose the convention as a ledger decision, then continue — otherwise every slice invents
  a dialect and the codebase becomes untranslatable to future models.
- Deferred work is legal only as a ledger entry, never as a bare code comment:
  **`TODO_LEDGER.md`**: `ID | what was deferred | why | trigger that makes it due | date`.
  A TODO with no trigger is a wish; refuse to record it until it has one.

### Phase 3 — Wire

Run the five-link trace from the `wire-check` skill on everything the slice added:
**Exists → Registered → Routed → Invoked → Reachable**, tracing from the system's real entry point
inward. New code that exists but is unreachable is the slice's failure, not a footnote. If
`wire-check` is installed, invoke it; if not, perform the five links manually and say so.

### Phase 4 — Prove

- Execute the proof line from Phase 1. Paste the actual output (or its relevant excerpt) into the
  slice report — a described result is **(trace-only)** and does not close the slice.
- Exercise at least one error path the slice claims to handle.
- If execution is impossible in the current environment (no runtime, missing credentials), the
  slice closes at **(trace-only)** *with that limitation stated in bold at the top of the report*
  and a ledger TODO whose trigger is "first environment that can execute".

### Phase 5 — Commit

- **Read the entire diff as its own reviewer before committing** (the short leash — non-negotiable
  for generated code): every changed line must be both explainable and intended. A line you cannot
  explain does not ship; a line you did not intend is a finding, not a freebie.
- One slice, one commit (or one clearly bounded changeset). The message states the behavior change
  and the proof line result, not the file list.
- The committed state must be **rollback-ready**: reverting this commit alone returns the system
  to its previous working state. Slices that entangle with uncommitted neighbors violate this.
- Update `ARCHITECTURE.md` only if the slice changed structure; update it in the same commit so
  document and code never diverge.

## Resuming an interrupted build

Before writing anything: read `TODO_LEDGER.md`, the last slice's proof line, and `git log`/diff of
uncommitted work. Re-prove the last claimed-working slice before stacking on it
(decay rule, PROTOCOL §1: a **(proven)** from a changed environment or code state is **(trace-only)** now).

## Rules

- No slice begins while the previous slice is unproven.
- A failing proof never gets "fixed" by weakening the proof line; it gets fixed by fixing the code,
  or by escalating to the director if the requirement itself looks wrong (violation vs deviation:
  a wrong requirement is a framing issue, route it to `problem-framing`).
- Generated code is held to the same standard as handwritten code; "the model wrote it" is not a
  provenance that lowers the bar.
- End every slice with: `SLICE <name>: proven | trace-only(reason) | failed(at link/phase)`.

## Anti-patterns this skill exists to kill

Big-bang builds proven only at the end; orphan modules awaiting a caller that never comes; happy-
path code; TODO comments that rot; commits that can't be reverted in isolation; "it should work"
as a completion claim.
