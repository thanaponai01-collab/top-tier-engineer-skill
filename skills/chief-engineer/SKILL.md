---
name: chief-engineer
description: >
  The dispatcher that turns ten specialist engineering skills into one top-tier engineer. Use at
  the start of ANY substantial engineering request — "build me X", "fix this", "is this good?",
  "make it faster", "continue the project" — whenever it is unclear which lifecycle stage applies,
  whenever a request spans multiple stages ("build and test it"), whenever resuming a project after
  a gap or in a fresh session, and whenever the user asks "where are we?" or "what's next?". If no
  other lifecycle skill has clearly and singularly triggered, this skill decides which one governs.
---

# Chief Engineer

One engineer, not ten tools. This skill reads the ground truth, classifies the request, routes it
through the right specialist skill(s) in the right order, and enforces the handoffs — so the user
talks to an engineer and the lifecycle happens underneath.

Shared rules, vocabulary, ledger registry, and the handoff chain live in `PROTOCOL.md` at the
suite root — read it once per session. (Gloss: evidence tags are **(proven)** executed /
**(trace-only)** read / **(assumed)** unverified.)

## Operating contract

1. **Route by artifact state, not by request phrasing.** Users say "build it" when there is no
   brief, "fix it" when nothing reproduces, "review it" when nothing is wired. The lifecycle stage
   is determined by what artifacts exist and what the request actually needs — never by the verb
   the user happened to use.
2. **Never skip a missing stage silently.** If the request needs an input that doesn't exist
   (code without a brief, optimization without a gate), either run the producing skill first —
   announced, in the same session — or proceed with the gap logged **(assumed)** and the cost of
   being wrong stated. Which of the two: apply meta-skills Discipline 3 (the asymmetry test).
3. **Lightweight by default.** For small requests, run the producing skill in compressed form
   (a three-line brief is still a brief) rather than refusing or bureaucratizing. The lifecycle
   scales down; it never disappears.
4. **One report.** However many skills run, the user receives one director-readable report: what
   was done, what was proven, what needs a decision — then depth.

## Phase 1 — Read the ground

Census the project root before classifying anything:

- Which ledgers from the PROTOCOL registry exist? Read the ones that exist (briefs and
  architecture fully; append-only ledgers from the tail).
- From the census, infer the lifecycle state:

| Artifacts present | Inferred state |
|---|---|
| none | pre-framing |
| brief + assumptions only | framed, undesigned |
| + architecture + decision ledger | designed, unbuilt (or mid-build: check commits/TODO ledger) |
| + slices/commits + TODO ledger | building |
| + correctness verdict (pass) | gated — eligible for perf, review, ship |
| + maint log | live system — maintenance mode is the default lens |

- Drift check: if artifacts contradict the code or each other, that finding outranks the user's
  request and is reported first (precedence: measurement > code > ledger > docs > recollection).

## Phase 2 — Classify the request

| Request shape | Route |
|---|---|
| New project / new feature / vague intent | problem-framing → arch-design → build-discipline → correctness-gate |
| Structural or technology choice | arch-design |
| "Build / implement / add / make it work" | build-discipline (after Rule 2 check on brief + architecture) |
| "Is it connected / hooked up / why is nothing happening" | wire-check |
| "Is it correct / test it / it's done?" | correctness-gate |
| "It's broken / wrong output / crashes / worked yesterday" — cause unknown | debug-protocol → evolve-maintain |
| Bug with known cause, dependency update, refactor, incident | evolve-maintain |
| "Slow / expensive / heavy / optimize" | perf-optimize (only past a passed gate; else gate first) |
| "Review / audit / is this code good / second opinion" | senior-review |
| "Where are we / what's next / resume" | this skill alone: state report + recommended next stage |

Multi-stage requests ("build and test it") become an announced pipeline. Ambiguous requests are
classified by Phase 1 state, and the classification is stated in one line so the user can redirect
cheaply — never ask which skill to use; that is this skill's job.

## Phase 3 — Execute the route

- Run each routed skill by its own contract; this skill adds no rules to theirs.
- At each handoff, verify the produced artifact actually satisfies the consumer's input (a brief
  with no falsifiable criteria does not satisfy arch-design — bounce it back, don't pass it on).
- Parallel gates before any "ship" declaration: correctness-gate (is it provably right?) and, when
  the user signals stakes, senior-review (is it wise?). Neither substitutes for the other.

## Phase 4 — Report

Lead with three sentences (done / proven / needs-decision), then the routed skills' own verdicts,
then depth. End with the state line:

`LIFECYCLE: <stage> | next: <skill or "director decision"> | blocked(missing: …) — if blocked`

## Anti-patterns this skill exists to kill

Coding from a verb instead of a state; ten skill reports stapled together instead of one engineer's
report; bureaucratizing a 20-line script through five ceremonies; skipping framing because the user
sounded confident; asking the user to pick a skill.
