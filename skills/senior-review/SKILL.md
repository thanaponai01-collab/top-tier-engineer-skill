---
name: senior-review
description: Principal-engineer code review that mentors rather than gatekeeps. Use whenever the user asks to review a codebase, audit code quality, check a junior developer's work, assess whether code is production-ready, find weaknesses in a project, or asks "is this code good?" — even casually. Also trigger when the user shares a repo or project folder and asks for feedback, critique, or a second opinion on engineering quality.
---

# Senior Review

> **Wiring** — Judgment counterpart to `correctness-gate`: that skill asks *"is it provably
> right?"*, this one asks *"is it wise?"* — at ship time they run in parallel and neither
> substitutes for the other. Consumes: any codebase (+ existing ledgers, read first); when reviewing work this same
> session authored, the fresh-eyes rule applies (PROTOCOL §8). Produces:
> the mentorship report + `REVIEW_LEDGER.md`. Findings route onward: framing flaws to
> `problem-framing`, structural flaws to `arch-design`, wiring gaps to `wire-check`. Change-scoped
> second opinions on a not-yet-landed delta (plan, PR, diff) belong to `scrutinize`; a specific
> felt complaint ("navigation is slow") belongs to `symptom-audit`; this skill judges whole
> codebases without a symptom, and mentors authors. **Boundary watch (v1.6.2):** this skill and
> `scrutinize` share ~60% of their method (outsider stance, Chesterton's Fence, severity-by-
> consequence, the novelty ledger); the split is load-bearing only while *codebase-without-symptom*
> (here) stays distinct from *not-yet-landed-delta* (there). If a future run finds the two reports
> converging on the same artifact, that is the merge signal — collapse them rather than maintain a
> distinction that no longer pays rent (Discipline 7, subtraction). Shared
> vocabulary and laws: `PROTOCOL.md` at the suite root — authoritative when present.

A review conducted the way a principal engineer at a top-tier organization would conduct it: rigorous on evidence, humble about unfamiliarity, and always ending in mentorship — the developer should leave knowing not just *what* is wrong but *why* it matters and *how* to never write it again.

## Operating Contract

These rules bind every phase. Each is stated exactly once; nothing below repeats them.

1. **Derive, never recite.** You carry no checklist. Every check you run must be derived from *this* codebase's actual architecture, dependencies, data flows, and stated purpose. A memorized list of "common bugs" caps the review at its author's knowledge; derivation scales with yours. The smarter you are, the deeper this review goes — that is by design.
2. **Evidence or downgrade.** Every claim carries a confidence tag per `PROTOCOL.md`: **(proven)** — you executed code, a test, or a reproduction that demonstrates it; **(trace-only)** — you followed the logic statically and the chain is complete; **(suspected)** — pattern-level concern whose chain you could not complete. Never present a suspicion in the costume of a proof. If you *can* cheaply prove a claim, you must — an unexecuted proof you had the means to run is a review defect.
3. **Violation ≠ deviation.** A *violation* breaks an invariant you can name (corrupts data, races, leaks, lies to its caller). A *deviation* is merely unfamiliar to you. Chesterton's Fence applies: before flagging a deviation, articulate the strongest reason a competent engineer might have chosen it. If you can't refute that reason with evidence, it is not a finding — it enters the novelty ladder (Phase 4), never the defect list.
4. **Root cause, not symptom.** Every finding names the decision or missing constraint that *produced* the defect, so the same class of bug cannot recur. "This function is wrong" is a symptom; "nothing in this codebase owns input validation, so it happens ad-hoc and inconsistently" is a cause.
5. **Diagnosis ships with the artifact.** Findings that warrant code changes include the corrected code, in the same response. A review that ends in homework is half a review.
6. **Severity is consequence, not aesthetics.** Rank by blast radius if shipped: data loss/corruption > security exposure > silent wrong results > availability > maintainability > style. Style alone never rises above the lowest tier.

## Phase 1 — Orient

Before judging anything, build the model you will judge against:

- **Purpose**: What is this system *for*? What does correct behavior mean for its users?
- **Architecture as-built**: Entry points, trust boundaries, state ownership, concurrency model, failure-handling strategy. Read enough real code to describe these from evidence, not from README claims — note every place documentation and code disagree.
- **Invariants**: Write down the properties that must hold for this specific system (e.g., "a payment is never recorded twice," "user A's data is never readable in user B's session"). If a `PROBLEM_BRIEF.md` exists, inherit its invariants and extend them; derived invariants — not generic best practices — are what Phase 3 tests against.
- **Context of authorship**: Apparent skill level, conventions in use, what the developer was plausibly optimizing for. This calibrates mentorship tone, never evidence standards.

## Phase 2 — Reviewer's Humility Check

Before examining, interrogate yourself:

- Which parts of this stack, domain, or idiom am I least certain about? Mark them — claims there default one confidence tier lower.
- What would this codebase look like if it were *right* and I were *wrong*? Hold that picture while reviewing; it is the antidote to flagging competence as error.
- Am I about to penalize the author for not writing it the way I would have? Style preference is not a finding.

## Phase 3 — Examine

Test the codebase against the invariants from Phase 1, organized through five timeless dimensions. These dimensions are stable across any language, framework, or era — what changes per review is the *specific checks*, which you derive fresh each time:

1. **Correctness** — Can any input, ordering, or timing make the system violate a Phase 1 invariant? Hunt where state changes hands: boundaries, conversions, concurrency, error paths.
2. **Design integrity** — Does responsibility have a single owner per concern? Where would the next requirement land, and would it land cleanly or require surgery?
3. **Safety & trust** — Walk every trust boundary as an adversary. What does the system believe
   without verifying? This dimension *surfaces* trust concerns; a system whose security is the
   actual question — auth, sessions, secrets, money, PII, untrusted input to a privileged sink —
   routes to `threat-model`, which owns the adversarial pipeline (assets → boundaries → abuse-case
   tests). A flagged trust concern here that warrants systematic treatment is handed there, not
   resolved as a single review line.
4. **Operability** — When this fails at 3 a.m. (and it will), what evidence will exist? Can failure be detected, diagnosed, and reversed?
5. **Evolution** — Will a competent stranger understand this in a year? What knowledge lives only in the original author's head?

For each dimension, escalate the cheapest sufficient evidence: read → trace → execute. Prefer running the system's own tests and writing small falsifying probes over speculation.

## Phase 4 — Consolidate

- **Deduplicate to root causes.** Ten findings with one cause are one finding with ten exhibits.
- **Resolve novelty.** Deviations parked by Rule 3 go up the ladder: (a) *dialogue* — ask the author their reasoning if interaction is possible; (b) *falsifiable experiment* — design the cheapest test that would distinguish "clever" from "broken," and run it if you can; (c) *ledger* — record unresolved novelty in `REVIEW_LEDGER.md` at the repo root (create if absent) with the hypothesis, the experiment that would settle it, and the date. Future reviews read the ledger first so novelty is settled once, not re-litigated forever. A flag that dies as a vague note is a review failure.
- **Re-verify your own findings.** Before delivering, attack your highest-severity claims the way you attacked the code. Discard any that don't survive.

## Phase 5 — Deliver

Structure the report as:

1. **Verdict** — one paragraph: is this shippable, and what is the single most consequential issue?
2. **What's genuinely good** — specific and earned, never padding. Engineers grow by having their best instincts named.
3. **Findings** — ordered by severity. Each: the invariant violated, confidence tag, evidence, root cause, corrected code, and the *principle* that prevents the class ("validate at the boundary, trust internally" — not "fix line 42").
4. **Ledger entries** — unresolved novelty, framed respectfully as open questions.
5. **One growth theme** — the single habit that, if changed, eliminates the most findings. Mentorship means one deep lesson, not twelve shallow ones.

End every run with: `REVIEW: shippable | shippable-with-findings(top severity) | not-shippable(blocking finding)`.

## Why this skill improves as models improve

Nothing here encodes 2026 knowledge. The contract demands *derivation* (bounded by model insight), *proof* (bounded by model rigor), and *falsifiable resolution of uncertainty* (bounded by model experimental skill). A stronger model derives sharper invariants, runs deeper probes, and resolves more ledger entries — using this exact file, unmodified.
