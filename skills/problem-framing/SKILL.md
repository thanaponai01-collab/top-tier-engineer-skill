---
name: problem-framing
description: >
  Turn a vague human intent into a buildable, falsifiable problem specification before any architecture or code exists. Use when a project starts, requirements feel fuzzy/contradictory, or a build drifted and nobody can state what "done" means.
---

# Problem Framing & Requirements

> **The question:** What are we actually building, stated so it can be proven wrong?  ·  Inputs, outputs and who runs next: `PROTOCOL.md` §4.

## When not to use this

an existing brief that only needs a decision → `arch-design`; a build already underway that drifted → `chief-engineer` (it decides whether framing reopens); a felt complaint about running software → `symptom-audit`.

## The job

You are the engineer who refuses to build the wrong thing efficiently. What you produce is not code
and not architecture — it is a **problem brief** precise enough that someone who never saw this
conversation could build from it. You ask the smallest number of questions that would change what
gets built, you turn every vague wish into a criterion that can be proven wrong, and you write down
what you will deliberately NOT build. Evidence tags per `PROTOCOL.md`.

## Steps: Extract → Interrogate → Constrain → Specify → Contract

### Phase 1 — Extract

Pull from the user's words (and any existing code, docs, or ledgers):

- **The job**: what the person actually wants to be true afterwards, stated as a change in the
  world rather than a feature. ("Sales staff stop re-typing orders" — not "build an order form.")
- **Who touches it**: people, other systems, AI agents. Where an AI is one of them (it calls the
  APIs, reads the logs, writes the code), say so — those interfaces have requirements of their own:
  errors a machine can parse, formats that don't vary.
- **What already exists**: if there is a codebase or an earlier record, read it before asking
  anything. A question the files already answer is a wasted question.

### Phase 2 — Ask (which questions, and in what order)

Only ask questions whose answers would change what gets built. Rank them in this order and ask from
the top, all in one message, never more than five:

1. **Questions that change direction** — answers that flip the architecture or the scope ("one user
   or many organizations?")
2. **Questions that remove the biggest unknown** ("does the old API let us write to it?")
3. **Questions that set the edges** — what is out of scope ("will offline mode ever be needed?")
4. ~~Preference questions~~ — colours, names, nice-to-haves. Don't ask; propose a default and mark
   it **(assumed)**.

If the user can't answer, don't stall: record the unknown (§3) with the default you chose and the
cost of being wrong.

### Phase 3 — Constrain

Split the spec into two lists, with a strict rule for what goes where:

- **Invariants** — things that, if broken, mean the project failed. Each one must be testable.
- **Preferences** — everything else. Preferences can be traded away during the build; invariants
  cannot, and changing one takes the director's explicit agreement.

Then write **what we will not build**: a short list of plausible things this project deliberately
leaves out. That list is what stops the scope creeping six months from now, when someone else is
maintaining the system.

### Phase 4 — Specify

Turn every invariant into an **acceptance criterion that could be proven wrong** — a sentence a
machine could check. Words banned from criteria: *fast, clean, intuitive, robust, scalable,
user-friendly*. Each one names a measurement and a threshold, or a behavior you can observe:

> ❌ "Search should be fast."
> ✅ "Search over 10k records returns first results in under 300 ms on the target hardware. **(assumed: 10k is realistic ceiling — confirm)**"

Include criteria for the things that go wrong: what must happen on bad input, on partial failure,
and when there is nothing to show. A spec that only describes success is half a spec.

### Phase 5 — Contract

Two artifacts — inline in the report under their own headings, or as files when §3 warrants:

**`PROBLEM_BRIEF.md`** — sections in this order:
1. The job, in one plain paragraph the director can read
2. Who touches it
3. Invariants (numbered, each with its acceptance criterion)
4. Preferences (numbered, marked as tradeable)
5. What we will not build
6. Open questions — only the ones the director must eventually answer

**Assumptions** — kept up to date, one row per assumption, in the report or in the project's notes
per §3:
`ID | assumption | default chosen | cost if wrong | status (open / confirmed / disproved) | date`

Later skills have to check this list. An **(assumed)** entry that turns out to be false is a
failure of the framing, not of the build — send it back here.

**Verdict noun:** `BRIEF`

End every run with a `BRIEF` line (PROTOCOL §5): `done(<N> invariants, <M> open questions)`, or
`blocked(contradictory: …)` when the request contradicts itself and only the director can settle
it.

## Rules

- A requirement said twice in different words is one requirement; merge it and keep one ID.
- If the user's request contradicts an invariant already in the brief, say so — never quietly go
  with whichever they said most recently.
- Never let the brief grow past what is needed to start the architecture. Framing that starts
  designing is doing the next skill's job.

## Common mistakes

"Requirements" that are really feature lists; asking 20 questions when 3 would change the build;
specs that say nothing about what happens when things fail; assumptions that live only in the chat
and disappear when the conversation ends.
