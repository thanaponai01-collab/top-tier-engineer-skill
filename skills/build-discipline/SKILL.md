---
name: build-discipline
description: >
  Execute a build in small, provable, fully-wired increments. Use when writing/generating code for a feature, tool, or system, or resuming a half-finished build. Trigger on "build it", "implement this", "add the feature", "make it work".
---

# Build Discipline

> **The question:** Is each piece proven and connected before the next one starts?  ·  Inputs, outputs and who runs next: `PROTOCOL.md` §4.

## When not to use this

no brief or no architecture yet → `problem-framing` / `arch-design` first (or an announced inline compression of them); cause of a failure unknown → `debug-protocol`; a throwaway answer to a question → spike mode, owned by `chief-engineer`.

## The job

You are the builder who never leaves code nothing calls. Work moves in **slices** — a slice is the
smallest piece that can be proven working end to end — and a slice is not done until it is
connected, run, and committed in a state the system could ship from. You build against the brief
and the architecture as this run received them — inline in the report, or as files where §3
warranted them; anywhere you depart from either, say so rather than slipping it in quietly. Every
"it works" claim carries **(proven)** or **(trace-only)** per `PROTOCOL.md` — and inside this
skill, only **(proven)** closes a slice.

## Steps per slice: Plan → Build → Wire → Prove → Commit

### Phase 1 — Plan the slice

- Pick the smallest unit of work that produces an observable behavior change reachable from the
  system's real entry point. "Half a backend with no caller" is not a slice; "one endpoint, wired,
  returning real data for one case" is.
- State the slice's **proof line** before writing code: the exact command, request, or interaction
  that will demonstrate it works, and what output counts as success. If you can't state the proof
  line, the slice is too vague to build.
- Check the recorded assumptions and decisions (§3) for anything this slice touches. Building on an
  open assumption is allowed; building on one without noticing is not.

### Phase 2 — Build

- **Smallest change that satisfies the proof line** (meta-skills Discipline 7, simplicity): delete
  or reuse before you add; add an abstraction on its second real use, not its first guess; "might
  need it later" is a deferred row with a trigger (§3), never structure written on a guess.
- **Simple first is an order, not a limit.** Take the simplest version that satisfies the proof
  line, then let evidence pay for anything deeper: a known limit on it closes as a deferred row
  whose trigger is **measured** (`p95 > 300 ms at 10k rows`), not feared. Structure added before
  that measurement exists is a guess about where the cost is — the same guess `perf-optimize`
  Phase 3 forbids later, so do not create it here.
- **Check where the change lands before taking the smallest one** (§8, the ratchet rule).
  "Smallest change" is measured against the slice, not against the file it goes into, so when that
  file is already overloaded the rule points the wrong way: the smallest change into a structure
  that is already too big is almost always *making it bigger*, because that is the option that
  needs no new seam. Each one looks fine on its own and together they are fatal — this is how a
  codebase becomes unmaintainable with every slice proven. So before taking the smallest change,
  ask where it lands:
  - **The file is clean** → smallest change, unchanged. This is the normal case; do not invent
    refactors to satisfy a rule.
  - **The file already carries accepted debt** (`DEBT_LEDGER.md` / the structural baseline) → the
    smallest change borrows against that debt, it is not free. Pay it down first where you can:
    pull out the seam this slice needs, prove that, *then* add the behavior — often two slices,
    and the first has a real proof line, since a change that moves code without changing behavior
    is exactly the kind you can prove. If you grow the file anyway, the slice does not close
    quietly: it says what it added and the new measured number, and the debt ledger row is updated
    in the same commit.
  - **The file would cross a threshold because of this slice** → that is not debt, it is a new
    structural decision made mid-slice. Treat it as one: a new module boundary is `arch-design`'s
    call (Law 3 — a structure you don't recognise gets a question, not a silent fix).
  A slice may not create code no test can reach. Code that is impossible to test is not the same
  as code that is merely untested: no later gate can report it missing, because no later gate can
  see it (§8 rules 5 and 7). Here is the only place it can be refused.
- **Interfaces from ground truth, not memory**: verify an external dependency's interface against
  this environment's ground truth before coding against it (cutoff rule, PROTOCOL §1) — a
  remembered API is **(assumed)**.
- **Error paths first**: write what happens on bad input, missing dependency, and partial failure
  before polishing the happy path. Happy-path-only code is the largest single source of later
  incidents.
- **Let the names do the explaining**: a function whose name and signature don't explain it gets
  renamed before it gets a comment.
- New conventions are forbidden mid-slice. If the architecture's conventions don't cover a case,
  stop, propose the convention as a ledger decision, then continue — otherwise every slice invents
  its own style and nobody can read the codebase later.
- Deferred work counts only as a written row, never as a bare code comment:
  `ID | what was deferred | why | trigger that makes it due | date`, inline or in the
  project's notes per §3. Prefer a trigger a machine checks (an assert, a test, a gate
  threshold) over one a human must remember to re-read — a prose trigger fires only if
  someone happens to re-read the row at the right moment, which is why prose rows rot.
  A deferral with no trigger is a wish; refuse to record it until it has one.

### Phase 3 — Wire

Run the five-link trace from the `wire-check` skill on everything the slice added:
**Exists → Registered → Routed → Invoked → Reachable**, starting at the system's real entry point
and working inward. New code that exists but nothing can reach is the slice failing, not a
footnote. If
`wire-check` is installed, invoke it; if not, perform the five links manually and say so.

### Phase 4 — Prove

- Execute the proof line from Phase 1. Paste the actual output (or its relevant excerpt) into the
  slice report — a described result is **(trace-only)** and does not close the slice.
- Exercise at least one error path the slice claims to handle.
- If execution is impossible in the current environment (no runtime, missing credentials), the
  slice closes at **(trace-only)** *with that limitation stated in bold at the top of the report*
  and a ledger TODO whose trigger is "first environment that can execute".

### Phase 5 — Commit

- **Read the whole diff as if reviewing someone else's work before committing** — this is not
  optional for code a model generated. Every changed line must be one you can explain and one you
  meant to make. A line you cannot explain does not ship; a line you did not intend is a finding,
  not a bonus.
- One slice, one commit (or one clearly bounded changeset). The message states the behavior change
  and the proof line result, not the file list.
- The committed state must be **rollback-ready**: reverting this commit alone returns the system
  to its previous working state. Slices that entangle with uncommitted neighbors violate this.
- If the architecture was written to a file, update it only when the slice changed structure, in
  the same commit, so document and code never diverge.

## Resuming an interrupted build

Before writing anything: read the open deferrals, the last slice's proof line, and `git log`/diff of
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
  measured value. Silent growth of known debt is the failure §8 exists to catch, and a
  proven slice is not a licence for it.
- End every slice with a `SLICE <name>` line (PROTOCOL §5): `done` carries the §1 tag, a slice that
  did not hold is `findings(at link/phase)`.

Shape and wording: `PROTOCOL.md` §9. The opening says what now runs that did not before, and what
was deferred. The rows are the slices, one each: slice, its proof line, the §1 tag, what the
director can now do. Diffs and proof output go under `Detail`.

**Verdict noun:** `SLICE <name>`

## Common mistakes

Building everything at once and proving it only at the end; modules waiting for a caller that
never arrives; code that only handles the happy path; TODO comments nobody comes back to; commits
that can't be reverted on their own; "it should work" as a claim of done; and the slow one — fifty
proven slices all appended to the same overloaded file, until nothing in it can be tested or
moved.
