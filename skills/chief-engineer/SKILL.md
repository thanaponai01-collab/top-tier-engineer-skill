---
name: chief-engineer
description: >
  The dispatcher that turns seventeen specialist engineering skills into one top-tier engineer (eighteen total with the dispatcher). Use at
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
suite root — read it once per session. (Gloss: **(proven)** executed · **(trace-only)** read, chain complete ·
**(suspected)** chain incomplete, flag only · **(assumed)** unverified premise — log it.)

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
   was done, what was proven, what needs a decision — then depth. When a run completes, the report
   must cite the run-trace result: state the inferred request type and whether every required stage
   reported a verdict ("this was a build request; SLICE and GATE both present; run complete"). On
   `incomplete`, the report names the missing stage and either runs it or logs why it was skipped
   (assumption + cost, per Rule 2). Run `tools/run-trace.py` on the transcript to produce this
   — do not self-report completeness without it.

## Phase 0 — Locate and load

- Find the suite root per `PROTOCOL.md` §0 — plugin install: two directories above this file.
  Read `PROTOCOL.md` once per session; `MAP.md` only when orienting a human to the suite itself.
- To run a routed skill, open `<root>/skills/<name>/SKILL.md` and execute its contract in this
  session — skills are contracts to read, not functions to call. If the file is missing, perform
  the procedure from PROTOCOL §4's registry and say the contract file was unavailable.

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
| "Slow / expensive / heavy / optimize" — runnable system, single measurable dimension | perf-optimize (only past a passed gate; else gate first) |
| "N+1 / will this query scale / add an index / does this endpoint hit the DB hard" — a data-access change | data-tier (gates cost class from the plan, before a budget exists) |
| "Feels slow / clunky / takes forever" — an existing codebase + a felt complaint; unrunnable here, or spanning speed + cohesion + UX | symptom-audit → its spec executes via build-discipline / perf-optimize |
| "Review / audit this codebase / is this code good" | senior-review |
| "Is this a mess / spaghetti / maintainable" — or a completed build whose director cannot read the result | structure-gate (measures shape; runs parallel to senior-review — shape vs. wisdom — exactly as correctness-gate ⫫ senior-review is proof vs. wisdom) |
| "Is this secure / can this be abused / review the auth / we handle passwords/payments/PII" | threat-model (parallel security gate; mandatory before ship if a trust boundary exists) |
| "Deploy / release / ship it / push to prod / cut a version" | ship-gate (after correctness-gate, and threat-model if a trust boundary is touched) |
| "Migration / alter schema / rename column / backfill / change the model with prod data" | data-evolution (invoked by evolve-maintain or ship-gate) |
| "Second opinion / scrutinize this PR, diff, plan, design doc" — a delta, not a codebase | scrutinize |
| "Where are we / what's next / resume" | this skill alone: state report + recommended next stage |
| Question / explanation only — nothing will be built or changed | no lifecycle skill: answer directly, evidence-tagged; meta-skills still bind; no ledgers |
| "Explore / try / prototype / is X even possible?" | spike mode (below): timeboxed, quarantined, knowledge-only output |
| No owning skill (deploy infra, CI pipelines, data migration, copywriting…) | say so plainly; propose the nearest mandate or plain execution under meta-skills — never silently stretch a mandate |

Multi-stage requests ("build and test it") become an announced pipeline. Ambiguous requests are
classified by Phase 1 state, and the classification is stated in one line so the user can redirect
cheaply — never ask which skill to use; that is this skill's job.

### The fast path (Rule 3, made concrete)

A request qualifies when it is single-session, single-slice, and touches no existing ledger.
**Carve-out (LIVE_RUN_001 process fix):** the fast path is *forbidden* — regardless of size —
when the slice touches a **trust boundary** (auth, authorization, sessions, secrets, untrusted
input crossing into a privileged sink) or **persistent data shape** (schema, migration, stored
format). A 40-line diff can bypass authentication or corrupt stored data; such a slice routes
through `threat-model` and/or `data-evolution` even when it would otherwise qualify as fast-path.
Fast path = one pass, one report: a ≤5-line **inline** brief (job, invariant(s), proof line);
inline decisions recorded only for one-way doors; build per `build-discipline` with `wire-check`'s
five links walked inline; the proof line executed; one combined verdict block at the end. No
ledger files are created (scale rule, PROTOCOL §7) — the report carries the inline equivalents so
any future session can promote them to files verbatim. The fast path compresses ceremony, never
evidence: a proof line still executes, and every claim still carries its tag.

### Spike mode (legal throwaway)

A spike answers a question, not a requirement — and the suite makes it legal so it never has to
happen illegally. Contract: declared at the start (`SPIKE: <question> | timebox`); quarantined in
a separate directory or branch and never wired into the system (wire-check on a spike should
*fail*, by design); exempt from build-discipline's ceremony but not from evidence tags. Its only
durable output is knowledge: the answer lands in `DECISION_LEDGER.md` or `ASSUMPTIONS.md` (or
inline, per the scale rule), and the code is then deleted or kept only as a labeled reference.
Spike code never graduates by merge — if the answer is "build it," it is rebuilt under
build-discipline with the spike as a crib sheet. The undeclared spike — a prototype that quietly
becomes production — is the anti-pattern this mode exists to kill.

## Phase 3 — Execute the route

- Run each routed skill by its own contract; this skill adds no rules to theirs.
- At each handoff, verify the produced artifact actually satisfies the consumer's input (a brief
  with no falsifiable criteria does not satisfy arch-design — bounce it back, don't pass it on).
- Parallel gates before any "ship" declaration: correctness-gate (is it provably right?),
  `threat-model` when a trust boundary is touched (does it resist abuse?), and, when the user
  signals stakes, senior-review (is it wise?). None substitutes for another. The act of shipping
  itself — reversibility, blast radius, rollback — is owned by `ship-gate`, the last door. For a
  delta that hasn't landed yet, the cheap pre-gate is scrutinize — kill bad changes before they
  cost a build.

## Phase 4 — Report

Lead with three sentences (done / proven / needs-decision), then the routed skills' own verdicts,
then depth. End with the state line:

`LIFECYCLE: <stage> | next: <skill or "director decision"> | blocked(missing: …) — if blocked`

## Anti-patterns this skill exists to kill

Coding from a verb instead of a state; ten skill reports stapled together instead of one engineer's
report; bureaucratizing a 20-line script through five ceremonies; skipping framing because the user
sounded confident; asking the user to pick a skill.
