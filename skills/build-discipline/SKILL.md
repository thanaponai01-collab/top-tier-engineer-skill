---
name: build-discipline
description: >
  Execute a build in small, provable, fully-wired increments. Use when writing/generating code for a feature, tool, or system, or resuming a half-finished build. Trigger on "build it", "implement this", "add the feature", "make it work".
---

# Build Discipline

> **Wiring** — Stage 3 of the lifecycle. Consumes: `ARCHITECTURE.md` + `PROBLEM_BRIEF.md` (invoke
> their producers if absent, or log the gap per `chief-engineer` Rule 2), plus `DEBT_LEDGER.md`
> when one exists (Phase 2, carrying capacity). Produces: proven slices as rollback-ready commits,
> `TODO_LEDGER.md`, and debt-ledger updates for any slice that grew an accepted breach. Invokes:
> `wire-check` as the exit gate of every slice (Phase 3). Downstream: `correctness-gate`;
> `structure-gate` when a slice touched a host on the debt ledger. Shared vocabulary and laws:
> `PROTOCOL.md` at the suite root — authoritative when present.
> (Gloss: **(proven)** executed · **(trace-only)** read, chain complete · **(suspected)** chain incomplete, flag only · **(assumed)** unverified premise — log it.)

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
- **Simple first is a sequence, not a ceiling.** Take the simplest version that satisfies the proof
  line, then let evidence buy the depth: a known ceiling on it closes as a `TODO_LEDGER.md` row
  whose trigger is **measured** (`p95 > 300 ms at 10k rows`), not feared. Structure added before
  that measurement exists is a guess about where the cost lives — the guess `perf-optimize` Phase 3
  forbids downstream, so do not manufacture it upstream.
- **Carrying capacity — check the host before taking the smallest diff** (PROTOCOL §10, the
  ratchet rule). "Smallest diff" is measured against the slice, not against the file it lands in,
  so on an already-overloaded host it points the wrong way: the smallest diff into a structure
  that is already too big is almost always *making it bigger*, because that is the option
  requiring no new seam. Each such increment is individually defensible and collectively fatal —
  it is how a codebase becomes unmaintainable with every slice proven. So before taking the
  smallest diff, ask where it lands:
  - **Host is clean** → smallest diff, unchanged. This is the normal case; do not manufacture
    refactors to satisfy a rule.
  - **Host carries accepted debt** (`DEBT_LEDGER.md` / the structural baseline) → the smallest
    diff is a withdrawal against that ledger, not a free move. Prefer paying down first: extract
    the seam this slice needs, prove the extraction, *then* add the behavior — often two slices,
    and the first one has a real proof line, since an extraction that changes no behavior is
    exactly the kind of change that can be proven. If you extend the host anyway, the slice does
    not close silently: it names the withdrawal and its new measured value, and the debt ledger
    row is updated in the same commit.
  - **Host would newly breach because of this slice** → this is not debt, it is a fresh structural
    decision made mid-slice. Route it as one: a new module boundary is `arch-design`'s call
    (Law 3, violation ≠ deviation — an unfamiliar structure gets dialogue, not a silent fix).
  A slice may not create code that no test harness can address. Untestable *by construction* is
  not the same as untested: no later gate can report it missing, because no later gate can see it
  (PROTOCOL §10 rules 5 and 7). Refusing it here is the only place it can be refused.
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
- A slice that grew a file already on the debt ledger says so in its report, with the before/after
  measured value. Silent growth of known debt is the failure PROTOCOL §10 exists to catch, and a
  proven slice is not a licence for it.
- **Director-facing report? Open with the DELIVERY block** (`PROTOCOL.md` §11): `ASKED` (quoted verbatim), `DID`, `SO`, `COST` — one sentence each. A `SO` that does not answer `ASKED` is reported first and outranks every verdict below it. Exempt for isolated §8.2 gates.
- End every slice with: `SLICE <name>: proven | trace-only(reason) | failed(at link/phase)`.

## Anti-patterns this skill exists to kill

Big-bang builds proven only at the end; orphan modules awaiting a caller that never comes; happy-
path code; TODO comments that rot; commits that can't be reverted in isolation; "it should work"
as a completion claim; and the slow one — fifty individually-proven slices that append to the same
overloaded file until nothing in it can be tested or moved.
