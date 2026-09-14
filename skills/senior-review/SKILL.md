---
name: senior-review
description: >
  Principal-engineer code review that mentors rather than gatekeeps. Use to review a codebase, audit code quality, assess production-readiness, find weaknesses, or when a repo/project folder is shared for feedback, or asks "is this code good?".
---

# Senior Review

> **The question:** Is this a good design, and will it hold up?  ·  Inputs, outputs and who runs next: `PROTOCOL.md` §4.

## When not to use this

a change that hasn't landed yet (PR, diff, plan) → `scrutinize`; measured structural shape → `structure-gate`; proof of correctness → `correctness-gate`; a felt complaint → `symptom-audit`; dead code and layer breaches → `latent-audit`; "where is the ceiling / what should I build next" → `toptier-lens`. This skill judges a whole codebase and teaches its author.

A review done the way a principal engineer would do it: strict about evidence, honest about what you don't know, and always ending in something the author learns — they should come away knowing not just *what* is wrong, but *why* it matters and *how* not to write it again.

## The job

These rules bind every phase. Each is stated exactly once; nothing below repeats them.

1. **Work it out; don't recite a list.** You carry no checklist. Every check comes from *this* codebase's real architecture, dependencies, data flows, and stated purpose. A memorized list of "common bugs" limits the review to whatever its author knew; working it out yourself scales with what you know. The smarter you are, the deeper this review goes — that is deliberate.
2. **Evidence, or drop a level.** Every claim carries a confidence tag per `PROTOCOL.md`: **(proven)** — you ran code, a test, or a reproduction that shows it; **(trace-only)** — you followed the logic by reading and the chain is complete; **(suspected)** — something looks wrong but you could not complete the chain. Never dress a suspicion up as a proof. If you *can* prove a claim cheaply, you must — leaving a proof unrun that you could have run is a defect in the review.
3. **Broken is not the same as unfamiliar.** Something is *broken* when it breaks an invariant you can name (corrupts data, races, leaks, lies to its caller). Something is merely *unfamiliar* when you just haven't seen it done that way. Before flagging the second kind, state the best reason a competent engineer might have had for it. If you cannot disprove that reason with evidence, it is not a finding — it goes to the unfamiliar-choices steps in Phase 4, never onto the defect list.
4. **Cause, not symptom.** Every finding names the decision or the missing constraint that *produced* the defect, so the same kind of bug cannot come back. "This function is wrong" is a symptom; "nothing in this codebase owns input validation, so it happens in scattered, inconsistent ways" is a cause.
5. **The fix ships with the diagnosis.** Findings that call for code changes include the corrected code, in the same response. A review that ends in homework is half a review. That fix is a change like any other and closes under §7: reviewed, checked against every other surface with the same exposure, shown to gate on the system's real authority check, and ending in a `FIX` line — never handed over unchecked.
6. **Severity is consequence, not taste.** Rank by what happens if it ships: data loss or corruption > security exposure > silently wrong results > downtime > maintainability > style. Style alone never rises above the bottom. Measure consequence per PROTOCOL §1: how much worse this is than what the system *already deliberately allows the same caller* — never against your own idea of what a system like this ought to promise.

## Phase 1 — Orient

Before judging anything, build the model you will judge against:

- **Purpose**: What is this system *for*? What does correct behavior mean for its users?
- **The architecture as actually built**: entry points, trust boundaries, who owns which state, how concurrency works, how failures are handled. Read enough real code to describe these from evidence, not from what the README claims — and note every place the documents and the code disagree.
- **Invariants**: Write down the properties that must hold for this specific system (e.g., "a payment is never recorded twice," "user A's data is never readable in user B's session"). If a `PROBLEM_BRIEF.md` exists, inherit its invariants and extend them; derived invariants — not generic best practices — are what Phase 3 tests against. Say where each invariant came from: **inherited** (from a ledger or a brief), **evidenced** (this system's own code, policies, comments, or existing surfaces show it is trying to hold it), or **imported** (what systems like this usually promise — an (assumed) claim about intent, not a fact about this system). PROTOCOL §1 applies: when the system's own evidence contradicts an invariant (a permissive policy, a comment saying it is open on purpose, a surface that already exposes the data), settle that *before* Phase 3 cites it — either the system's intent contradicts itself, and that is the finding, or the invariant is narrowed. An imported invariant that the system's own evidence contradicts, unanswered, supports no severity at all.
- **Who wrote it and under what conditions**: apparent experience level, the conventions in use, what the developer was probably optimizing for. This sets the tone of your teaching, never the evidence standard.

## Phase 2 — Check yourself first

Before examining anything, ask:

- Which parts of this stack, domain, or style am I least sure about? Mark them — claims there drop one confidence level by default.
- What would this codebase look like if it were *right* and I were *wrong*? Keep that picture in mind while reviewing; it is what stops you filing competence as error.
- Am I about to penalise the author for not writing it the way I would have? A style preference is not a finding.

## Phase 3 — Examine

Test the codebase against the invariants from Phase 1, across five areas. The areas hold for any language, framework, or era — what changes each time is the *specific checks*, which you work out fresh:

1. **Correctness** — can any input, ordering, or timing make the system break a Phase 1 invariant? Look where state changes hands: boundaries, conversions, concurrency, error paths.
2. **Design** — does each concern have exactly one owner? Where would the next requirement land, and would it land cleanly or need surgery?
3. **Safety and trust** — walk every trust boundary the way an attacker would. What does the system
   take on faith without checking? This dimension *surfaces* trust concerns; a system whose security is the
   actual question — auth, sessions, secrets, money, PII, untrusted input to a privileged sink —
   routes to `threat-model`, which owns the adversarial pipeline (assets → boundaries → abuse-case
   tests). A flagged trust concern here that warrants systematic treatment is handed there, not
   resolved as a single review line.
4. **Running it in production** — when this fails at 3 a.m. (and it will), what evidence will exist? Can the failure be spotted, diagnosed, and undone?
5. **Changing it later** — will a competent stranger understand this in a year? What knowledge exists only in the original author's head?

In each area, use the cheapest evidence that settles it: read → trace → run. Prefer running the system's own tests and writing small probes that would prove you wrong, over speculating.

## Phase 4 — Consolidate

- **Merge findings down to their causes.** Ten findings with one cause are one finding with ten examples.
- **Settle the unfamiliar choices** parked by Rule 3, in this order: (a) *ask* — put the question to the author, if you can talk to them; (b) *test* — design the cheapest experiment that would tell "clever" apart from "broken", and run it if you can; (c) *record* — write the unsettled ones into `REVIEW_LEDGER.md` at the repo root (create it if it is missing) with the question, the experiment that would settle it, and the date. Later reviews read that file first, so each one is settled once instead of argued forever. A flag that fades into a vague note is a failed review.
- **Check your own findings again.** Before delivering, attack your highest-severity claims the way you attacked the code. Drop the ones that don't survive.

## Phase 5 — Deliver

Shape and wording: `PROTOCOL.md` §9. The opening carries three things no other skill owes: whether
it can ship and what the single biggest issue is; what is genuinely good — specific and earned,
never padding, because engineers grow by having their best instincts named; and the one habit that,
if changed, would remove the most findings. One lesson that goes deep, not twelve shallow ones.

One row per finding, ordered by severity. Columns: the invariant broken, the tag, the evidence,
the cause, and the *rule* that prevents this whole kind of bug ("check input at the boundary, trust
it inside", not "fix line 42"). Corrected code goes under `Detail`, and so do the unfamiliar
choices you could not settle, written respectfully as open questions.

**Verdict noun:** `REVIEW`

End every run with a `REVIEW` line (PROTOCOL §5).
