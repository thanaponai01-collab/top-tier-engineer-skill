---
name: improvement-backlog
description: >
  Carry findings out to an issue tracker and run the pickup loop. Use for "file these as issues", "output findings to the tracker", "work the backlog", "implement issue #N", or when findings must survive the session that found them.
---

# Improvement Backlog

> **Wiring** — The crossing between a finding and a tracker, and the loop back. Mandate within
> the suite: the audit and review skills answer *"what is wrong or improvable?"* and rank their
> own prescriptions; `build-discipline` answers *"how does an increment land proven?"*; this
> skill asks **"did the finding survive the crossing into a tracker intact, and did the close
> carry evidence?"** Consumes: findings already produced and ranked by their owning skill
> (`AUDIT_SPEC.md`, `LATENT_REPORT.md`, `REVIEW_LEDGER.md`, `STRUCTURE_REPORT.md`,
> `THREAT_MODEL.md`, `DATA_TIER.md`, a scrutiny report) — **or emitted by a tool or CI gate as a
> bare verdict line**, which has no prescription phase and is governed by contract rule 2's tool
> clause — plus the tracker of record. Produces: tracked issues — the tracker is the ledger;
> `BACKLOG.md` materializes only when no tracker exists (scale rule, one pointer line otherwise).
> Hands off: each picked issue re-enters `chief-engineer` for routing, exactly like a fresh
> request; a finding that arrives incomplete goes back to the skill that produced it, or — having
> no skill to return to — is completed per rule 2's tool clause or held. Shared vocabulary and laws: `PROTOCOL.md` at the
> suite root — authoritative when present. (Gloss: **(proven)** executed · **(trace-only)** read,
> chain complete · **(suspected)** chain incomplete, flag only · **(assumed)** unverified premise
> — log it.)

## Boundaries

**This skill authors no findings and re-ranks nothing.** Diagnosis, root-cause collapse,
impact-per-effort ordering, and the pre-written acceptance check are `symptom-audit`'s contract
and its siblings' — this skill carries what they produced and refuses what arrives without it
(see *Carry, never re-author*). Generating findings → the owning audit skills; if asked to hunt
with nothing in hand, `chief-engineer` fans out the audits first (PROTOCOL §8.2, parallel gates)
and this skill files the merged result. Implementing → `build-discipline` and peers, via
`chief-engineer`. Deferred work *inside* a build, with a trigger that makes it due →
`TODO_LEDGER.md`, owned by `build-discipline`; accepted structural debt → `DEBT_LEDGER.md`, owned
by `structure-gate`. Both are linked from an issue, never re-typed as one. "Where are we?" →
`chief-engineer`.

**Boundary watch against `symptom-audit`** (Law 3, violation ≠ deviation — a boundary is a
hypothesis until a run tests it): if a run ever finds that filing an issue requires *re-deciding*
a finding's rank or rewriting its acceptance check, this mandate is the wrong shape and the
residue belongs in `symptom-audit`'s Phase 6/7 as a delivery target. Log that in
`REVIEW_LEDGER.md` as the merge signal; do not absorb the decision silently.

One principle, everything else serves it: **an issue is a ledger row — Law 2, artifacts outlive
conversations — so it must let a future session with zero chat history implement it, and its
close must carry the evidence that it happened.**

## Operating contract

1. **Carry, never re-author** (Law 1, every rule lives in exactly one place). Every field an
   issue needs was already authored upstream: the evidence tag, the `file:line` location and its
   subject pin (PROTOCOL §1, the pin rule), the felt or measured cost, the acceptance check, and
   the finding's rank. This skill's work is the crossing — that each arrives intact, attributed
   to the artifact that produced it. Restating an upstream rule here would put it in two places;
   checking that its output survived is the job.
2. **Incomplete in, nothing out.** A finding missing its acceptance check is not filed — it goes
   back to its producer, named. "Investigate X" with no observable before/after is homework, and
   an issue is the wrong container for homework: it stays a watch-list line in the producing
   ledger until someone can say what would settle it.

   **A tool is a producer with no prescription phase, and rule 1 alone would strand its
   findings.** A CI gate, an analyzer, a linter, a cadence watcher — each emits a measurement and
   a verdict line, never a ranked prescription, so there is no producer to send an incomplete
   finding back to. Two consequences, and neither is a licence to start authoring: (a) the check
   is not authored but **derived — re-run the tool, the verdict line flips.** The tool is its own
   oracle, so deriving its check substitutes no judgment and does not breach rule 1. (b) The
   crossing must additionally name **any other gate the fix could flip**, because a tool reports
   its own signal and is blind to its neighbours, and no upstream artifact exists to catch that.
   Couplings the artifacts actually show are carried as checks; couplings merely suspected are
   carried as open questions in the issue, tagged as such — never as checks, which would dress a
   guess in a proof's costume. *Worked example, illustrative and overridable, not contract:
   bumping a CI action pin to clear a deprecation is checked by the annotation disappearing —
   and by `CADENCE: clean(N)` still holding, because that workflow's own comments record
   `fetch-depth: 0` as load-bearing for the release-mapping gate. The second check is the one
   that would otherwise fail silently.*
3. **The tag crosses unchanged.** An issue title stating a **(suspected)** concern as fact is a
   defect of this skill, not of the producer — the tracker is where a hedge is most likely to be
   lost, because a title is read alone. Titles are director-readable (Law 4, director-readable
   output) and carry the tag's honesty in words, not just a label.
4. **One issue per finding, provenance linked.** Findings the producer already collapsed to one
   root cause stay collapsed; findings from *different* producers that name the same cause are
   filed once and cross-linked, because neither producer could see the other. Order in the
   tracker is the producers' ranking, merged — this skill preserves it and states the merge rule
   it used, rather than substituting a judgment of its own.
5. **The close discipline** — the half no upstream skill owns, because it happens after they have
   all closed. An issue closes only with evidence in the closing comment: the verdict line(s) of
   the work that resolved it (`SLICE`/`GATE`, plus `FIX` per PROTOCOL §9 when the work was a
   delivered fix) and the executed result of the acceptance check the issue carried. A commit
   that mentions an issue is a citation, not a close. Closing as *won't-do* is legal and honest:
   it records why, so the finding is adjudicated once rather than re-discovered every audit.
6. **Tracker-agnostic** (Law 6, constrain process never intelligence): any tracker satisfies this
   contract, and `gh issue create --title … --body … --label …` is a worked example, not the
   rule. The tracker of record is declared once — in `BACKLOG.md` as a pointer line, or inline
   per the scale rule (PROTOCOL §7). No tracker and no repo? `BACKLOG.md` holds the same rows.

## Pipeline

**Filing:** *Gather* the producing artifacts (if none exist, this skill does not improvise them —
PROTOCOL §4: route through `chief-engineer` to run the owning audits first) → *Check* each
finding against rules 1–2, listing what was held back and why, so the director sees the judgment
rather than silence → *File* per rules 3–4, labelled by area and owning skill so the backlog is
sliceable → *State* the merge rule used and what the director will feel after the top item lands.

**Pickup:** *Pick* the top open issue or the director's named `#N` → *Route* it through
`chief-engineer` as the request (fast path and trust-boundary carve-outs apply unchanged) →
*Close* per rule 5 → *Re-check* whether landing it voided or unblocked other issues, and say so.

## Report

Director-readable lead (Law 4, director-readable output): how many findings arrived, how many
crossed versus were held back, what sits on top and whose ranking put it there — then the issue
list.

**Director-facing report? Open with the DELIVERY block, before any verdict** — `ASKED` (the
director's own words, quoted verbatim), `DID`, `SO`, `COST`. This is `PROTOCOL.md` §11, the sense
floor. Exempt when running as an isolated §8.2 gate reporting to a merging skill.

`BACKLOG: filed(N, top: <finding>) | picked(#id → <skill>) | closed(#id, <tag>) | clean(bar unmet) | blocked(no tracker: <reason>)`

## Anti-patterns this skill exists to kill

The issue dump (forty issues nobody implements); homework issues with no acceptance check; a
**(suspected)** flag laundered into a factual title; the evidence-free close ("done" with no
verdict line); re-auditing instead of filing what the audits already found; re-ranking a
producer's prescription by this skill's own taste; duplicating `DEBT_LEDGER.md` or
`TODO_LEDGER.md` rows as issues instead of linking them.

## Why this skill improves as models improve

Nothing here encodes a tracker, a stack, or a taxonomy: carry-don't-re-author, incomplete-in
nothing-out, close-with-evidence are method. A stronger model catches subtler losses in the
crossing, merges two producers' rankings more honestly, and writes closes a future reader can
audit — through this same file, unchanged.
