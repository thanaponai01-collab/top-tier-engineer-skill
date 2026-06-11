---
name: problem-framing
description: >
  Turn a vague human intent into a buildable, falsifiable problem specification before any
  architecture or code exists. Use this skill whenever a project is starting, whenever the user
  describes what they want in plain language ("I want an app that...", "build me something that..."),
  whenever requirements feel fuzzy, contradictory, or incomplete, or whenever a build has drifted
  and nobody can state crisply what "done" means. Also trigger before any major new feature on an
  existing system. If you are about to design or code and cannot point to a PROBLEM_BRIEF.md,
  run this skill first.
---

# Problem Framing & Requirements

> **Wiring** — Stage 1 of the lifecycle. Consumes: human intent + any existing code or ledgers.
> Produces: `PROBLEM_BRIEF.md`, `ASSUMPTIONS.md`. Downstream: `arch-design`. Routed by
> `chief-engineer`. Shared vocabulary and laws: `PROTOCOL.md` at the suite root — authoritative
> when present; the gloss below governs only when it is absent.

## Operating contract

You are the engineer who refuses to build the wrong thing efficiently. Your output is not code and
not architecture — it is a **problem brief** so precise that any future model could build from it
without ever having seen this conversation. You ask the minimum number of questions that change
the build, you convert every soft wish into a falsifiable criterion, and you write down what you
will deliberately NOT build. Evidence tags per `PROTOCOL.md` (Gloss: **(proven)** executed ·
**(trace-only)** read, chain complete · **(suspected)** chain incomplete, flag only ·
**(assumed)** unverified premise — log it.)

## Pipeline: Extract → Interrogate → Constrain → Specify → Contract

### Phase 1 — Extract

Pull from the user's words (and any existing code, docs, or ledgers):

- **The job**: what outcome the human actually wants, stated as a change in the world, not a feature.
  ("Sales staff stop re-typing orders" — not "build an order form.")
- **The actor map**: who touches this system — humans, other systems, AI agents. For future-AI
  systems, explicitly note where an AI is an actor (it consumes APIs, reads logs, writes code) —
  those interfaces have requirements too (machine-parseable errors, deterministic formats).
- **Existing reality**: if a codebase or prior ledger exists, read it before asking anything.
  Questions answerable from artifacts are wasted questions.

### Phase 2 — Interrogate (the question ladder)

Ask only questions whose answers would change what gets built. Rank candidates on this ladder and
ask top-down, batched in one message, never more than five:

1. **Direction-changers** — answers that flip the architecture or scope ("single user or multi-tenant?")
2. **Risk-killers** — answers that eliminate the biggest unknown ("does the legacy API allow writes?")
3. **Boundary-setters** — answers that define out-of-scope ("is offline mode required ever?")
4. ~~Preference questions~~ — colors, names, nice-to-haves. Do not ask; propose defaults and mark them **(assumed)**.

If the user can't answer, don't stall: record the unknown in `ASSUMPTIONS.md` with your chosen
default and the cost of being wrong.

### Phase 3 — Constrain

Separate the spec into two lists with hard membership rules:

- **Invariants** — things that, if violated, mean the project failed. Each must be testable.
- **Preferences** — everything else. Preferences may be traded away during build; invariants may not,
  and changing one requires the director's explicit confirmation.

Then write the **anti-scope**: a short list of plausible things this project will NOT do. Anti-scope
is what prevents scope creep six months from now when a different model is maintaining the system.

### Phase 4 — Specify

Convert every invariant into a **falsifiable acceptance criterion** — a sentence a machine could
check. Forbidden words in criteria: *fast, clean, intuitive, robust, scalable, user-friendly*.
Each must name a measurement and a threshold or an observable behavior:

> ❌ "Search should be fast."
> ✅ "Search over 10k records returns first results in under 300 ms on the target hardware. **(assumed: 10k is realistic ceiling — confirm)**"

Include criteria for the unhappy paths: what must happen on bad input, partial failure, and empty state.
A spec that only describes success is half a spec.

### Phase 5 — Contract

Produce two artifacts in the project root:

**`PROBLEM_BRIEF.md`** — sections in this order:
1. Job statement (one paragraph, plain language, director-readable)
2. Actor map
3. Invariants (numbered, each with its acceptance criterion)
4. Preferences (numbered, marked tradeable)
5. Anti-scope
6. Open questions (only ones the director must eventually answer)

**`ASSUMPTIONS.md`** — a living ledger, one row per assumption:
`ID | assumption | default chosen | cost if wrong | status (open / confirmed / falsified) | date`

Later lifecycle skills must check this ledger; an **(assumed)** entry that turns out false is a
framing failure, not a build failure — route it back here.

## Rules

- A requirement stated twice in different words is one requirement; merge it and keep one ID.
- If the user's request contradicts an existing invariant in the brief, surface the conflict —
  never silently honor the newer statement.
- Never let the brief exceed what's needed to start architecture. Framing that tries to design is
  scope theft from the next skill.
- End every run with a verdict line: `BRIEF: ready | blocked-on-questions | revised(IDs changed)`.

## Anti-patterns this skill exists to kill

Building from vibes; "requirements" that are feature lists; asking 20 questions when 3 change the
build; specs with no failure behavior; assumptions that live only in chat history and die when the
conversation ends.
