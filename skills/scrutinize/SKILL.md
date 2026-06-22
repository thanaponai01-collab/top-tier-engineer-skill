---
name: scrutinize
description: Outsider, change-scoped second opinion on a delta — a plan, PR, diff, design doc, or proposed change that has not yet landed. First asks whether the change should exist at all (do nothing, reuse what exists, smaller change, different layer), then traces the real code path end-to-end to verify the change does what it claims. Use whenever the user asks to scrutinize, review, audit, sanity-check, or get a second opinion on a PR, diff, plan, design doc, or proposed change — anything pre-merge or pre-build. For whole-codebase review and author mentorship, use senior-review instead; this skill judges a delta, not a codebase, and owes its author nothing.
---

# Scrutinize

> **Wiring** — Parallel gate, callable at any stage on any delta (plan, design doc, PR, diff,
> proposed change). Mandate within the suite: `senior-review` asks *"is this codebase wise?"* and
> mentors its author; this skill asks **"should this change exist, and does it do what it
> claims?"** — it serves the change's consumers, not its author. Consumes: the delta + its host
> system (+ ledgers, read first). Produces: the scrutiny report; unresolved novelty appended to
> `REVIEW_LEDGER.md` per its owner's schema. Findings route onward: intent/scope flaws →
> `problem-framing` or `arch-design`, wiring gaps → `wire-check`, unknown-cause breakage →
> `debug-protocol`, post-merge concerns → `senior-review` or `evolve-maintain`. **Boundary watch
> (v1.6.2):** this skill and `senior-review` share most of their method (outsider stance,
> Chesterton's Fence, severity-by-consequence, the novelty ledger); the split holds only while
> *delta-not-yet-landed* (here) stays distinct from *whole-codebase-without-symptom* (there).
> Stated from both sides per mandate-boundary discipline — if a run finds the two converging on one
> artifact, collapse them (Discipline 7, subtraction). Shared vocabulary
> and laws: `PROTOCOL.md` at the suite root — authoritative when present. (Gloss: **(proven)**
> executed · **(trace-only)** read, chain complete · **(suspected)** chain incomplete, flag only ·
> **(assumed)** unverified premise — log it.)

Stand outside the change and ask whether it should exist at all, then verify it actually does
what it claims, end-to-end. The diff is the entry point, never the scope.

## Operating stance

- **Outsider, not stranger to reason.** Borrow no confidence from the author, the PR description,
  or the plan's prose — read the artifact cold. But outsider does not mean unfamiliar = wrong:
  per Law 3 (violation ≠ deviation), before flagging an odd choice, articulate the strongest
  reason a competent engineer might have made it, and check `DECISION_LEDGER.md` and
  `ASSUMPTIONS.md` first — a "surprise" the ledger already explains is archaeology, not signal.
  Unrefuted, an odd choice is a question for the report, never a finding. And when this same
  session authored the delta, true outsiderness requires fresh eyes (PROTOCOL §8): run this skill
  in a fresh context given artifacts only, or mark the report `(same-context review)`.
- **End-to-end, not diff-local.** Follow the call graph through real code paths, including the
  unchanged code on either side of the diff — bugs hide at the seams.
- **The artifact's claims are quotes; your verdicts carry tags.** "The PR says X" is a claim.
  "I walked X: …" is **(trace-only)**. "I ran X: …" is **(proven)**. Never let the first wear the
  costume of the others — and if execution is one cheap command away, trace-only is not an
  acceptable final answer.
- **Actionable, concise, with rationale.** Every finding states what to change, why it matters,
  and the evidence that exposed it. No filler, no restating the diff back.

## Workflow — run in order, never skip ahead

### 1. Intent — should this exist at all?

- State the goal in one sentence, in your own words. If you cannot, the delta is underspecified:
  stop, report `SCRUTINY: blocked(underspecified: what's missing)`, and route to
  `problem-framing` for the missing criteria.
- Run the subtraction pass (meta-skills Discipline 7) on the whole change, top-down:
  1. **Do nothing** — is the problem real and load-bearing, or inherited from a stale assumption?
  2. **Reuse** — does something in this codebase already do this? New surface needs a reason.
  3. **Shrink** — is there a change that gets 90% of the goal at 10% of the risk?
  4. **Relocate** — does this belong at a different layer (config vs code, framework vs app,
     build vs runtime)?
- A better alternative, named with rationale, is the single most valuable output this skill can
  produce — surface it *before* any line-by-line work, as the report's lead.

### 2. Trace — walk the real path

- For each behavior the delta claims, trace end-to-end through the actual code: entry point →
  call sites → branches taken → state mutated → exit, return, or side effect.
- For a plan or design doc: trace the proposed flow against the existing system. Every assumption
  the plan makes that the code does not support is a finding; tag what the plan never checked as
  **(assumed)** and log it.
- Note every place the trace surprises you — unexpected branch, dead code reached, state you
  didn't know existed. After the ledger check from the stance above, remaining surprises are
  signal.

### 3. Verify — does it do what it claims?

For each claim, in this exact shape: *"Claims X. Path: A → B → C. At C, [observation] (tag).
Therefore holds / does not hold."* Then attack:

- **Breaking inputs and states** — empty, null, unicode, huge, concurrent callers, error paths,
  partial failure, retries, ordering assumptions.
- **Silent changes** — performance, error semantics, observability, contracts for other callers,
  on-disk or on-wire formats. A delta is responsible for everything it changes, not just what it
  mentions.
- **The tests** — do they exercise the path you traced, or pass around it (mocks hiding the
  seam, asserts on intermediate state, happy path only)? A green test that skips the traced path
  is itself a finding.
- Escalate read → execute wherever cheap: run the test, fire the request, import the module.

### 4. Report

Lead with the simpler alternative if one survived step 1. Then one tight block per finding,
ordered by consequence (blocker → major → nit; consequence scale per `senior-review` Rule 6):

- **Finding** — one sentence, specific, with `file:line` where applicable.
- **Why it matters** — the consequence, not the principle.
- **Evidence** — the trace step, input, or executed command that exposed it, with its tag.
- **Change** — concrete and minimal; per Law 5 (diagnosis ships with the artifact), when the fix
  is small, ship the corrected lines here, not as homework.

End every run with: `SCRUTINY: ship | fix-then-ship(top finding) | rework(reason) | reject(reason) | blocked(underspecified: what's missing)`.

## Rules

- **No rubber-stamps.** "LGTM" is not an output. A clean pass lists what was traced and what was
  executed, so the reader can judge whether the scrutiny covered the surface they cared about.
- **Cite or it didn't happen.** Every claim about the code names a path, file, line, or command.
  "Might break under load" without a mechanism is **(suspected)** at best, and says so.
- **The step-1 pass is mandatory**, even for small deltas — skipped only on an explicit "don't
  question scope," and the report then states it was skipped.
- **Structure outranks nits.** If step 1 or 2 surfaces a structural problem, lead with it and
  drop the nits; polishing a change that shouldn't exist is the anti-pattern.
- **No flattery, no hedging.** Mentorship and earned praise live in `senior-review`; this report
  serves whoever must live with the change.

## Why this skill improves as models improve

Nothing here encodes a stack or an era: intent restatement, the subtraction ladder, end-to-end
tracing, and claim-by-claim verification are method. A stronger model restates intent more
sharply, finds smaller equivalent changes, traces deeper seams, and executes more of the
verification — through this same file, unchanged.
