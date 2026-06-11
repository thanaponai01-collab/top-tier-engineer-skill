# PROTOCOL.md — The Shared Layer

This file is the **single authoritative statement** of everything the twelve skills share.
Per Law 1 below, no skill restates what is written here; skills carry at most a one-line gloss
for graceful degradation (see §6). When a skill and this file appear to disagree, this file wins
and the disagreement is reported as a defect in the skill.

---

## 0. Locating and loading this layer

Resolution order, checked once per session by whichever skill of this suite runs first:

1. **Plugin install** — the suite root is two directories above any skill's `SKILL.md`
   (`<root>/skills/<name>/SKILL.md` → `<root>/PROTOCOL.md`, `<root>/MAP.md`).
2. **Loose install** — `PROTOCOL.md` sits alongside the copied skill folders
   (e.g. `~/.claude/skills/PROTOCOL.md`).
3. **Absent** — the skill's own gloss governs (§6), and the run states that once.

**"Invoking" a skill means:** open `<root>/skills/<name>/SKILL.md` and execute its contract in the
current session. Skills are contracts to read, not functions to call. If the contract file cannot
be found, perform the procedure named in the §4 registry from this file's description of it, and
state that the contract file was unavailable — never silently skip the stage.

## 1. Evidence vocabulary (used identically everywhere)

| Tag | Meaning | Strength |
|---|---|---|
| **(proven)** | Demonstrated by actually executing something — a test, a command, a reproduction, a profile run — and observing the result. | Strongest |
| **(trace-only)** | Concluded by reading code/docs/logs without execution; the reasoning chain is *complete*. Honest, but weaker. | Middle |
| **(suspected)** | A pattern-level concern whose reasoning chain is *incomplete*. Admissible only as a flagged concern, never as a finding or verdict. | Weak |
| **(assumed)** | A premise nobody verified. Must be logged in `ASSUMPTIONS.md`; never silently relied on. | Premise, not evidence |

Decay rule: **(proven)** is bound to the environment, code state, and session that produced it.
When any of those changes, it decays to **(trace-only)** until re-demonstrated.

## 2. The Laws

1. **Every rule lives in exactly one place.** A skill never repeats itself; a project never has
   two sources of truth; this suite's shared rules live only in this file.
2. **Artifacts outlive conversations.** Ledgers are the institutional memory. Any future model,
   with zero chat history, must be able to resume from the artifacts alone.
3. **Violation ≠ deviation.** A concrete failure (broken invariant, proven bug, missed
   requirement) is treated differently from an unfamiliar-but-possibly-valid approach
   (Chesterton's Fence). Deviations get dialogue or falsifiable experiments, never silent "fixes".
4. **Director-readable output.** Every report's verdict and summary must be understandable by a
   non-coder directing the build. Detail may be technical; conclusions may not.
5. **Diagnosis ships with the artifact.** Identifying a problem obligates delivering the fix or
   patched artifact in the same response wherever feasible.
6. **Constrain process, never intelligence.** Skills specify phases, evidence rules, and stop
   conditions — never solutions. A stronger model inside the same contract produces strictly
   better results.

## 3. Ledger registry

One owner per ledger; the owner skill defines the schema, everyone else reads/appends per that schema.

| Ledger (project root) | Owner skill | Holds |
|---|---|---|
| `PROBLEM_BRIEF.md` | problem-framing | Job, actors, invariants, acceptance criteria, anti-scope |
| `ASSUMPTIONS.md` | problem-framing | Every (assumed) premise, default chosen, cost if wrong, status |
| `ARCHITECTURE.md` | arch-design | Current structural truth (always overwritten; history in decision ledger) |
| `DECISION_LEDGER.md` | arch-design | Append-only consequential decisions with options + reversibility |
| `TODO_LEDGER.md` | build-discipline | Deferred work, each entry with a trigger that makes it due |
| `CORRECTNESS_VERDICT.md` | correctness-gate | Latest gate result, oracle table, mutation results, residual risk |
| `PERF_BUDGET.md` | perf-optimize | Budgets, currents, guards per dimension |
| `REVIEW_LEDGER.md` | senior-review | Unresolved novelty: hypothesis + the experiment that would settle it |
| `MAINT_LOG.md` | evolve-maintain | Append-only intervention history: symptom → root cause → treatment |

## 4. The handoff chain

| Skill | Consumes | Produces | Hands off to |
|---|---|---|---|
| chief-engineer | any request + artifact census | routing decision, state report | the routed skill(s) |
| problem-framing | human intent, existing artifacts | PROBLEM_BRIEF.md, ASSUMPTIONS.md | arch-design |
| arch-design | brief + assumptions | ARCHITECTURE.md, DECISION_LEDGER.md | build-discipline |
| build-discipline | architecture + brief | proven slices, commits, TODO_LEDGER.md | correctness-gate (invokes wire-check per slice) |
| wire-check | a slice or suspect component | chain table, connecting code | the invoking skill |
| correctness-gate | criteria, contracts, proof lines | CORRECTNESS_VERDICT.md, test suite | perf-optimize / ship / senior-review |
| debug-protocol | an observed failure | Cause Verdict (proven root cause) | evolve-maintain (the fix) |
| perf-optimize | a passed gate + a budget | PERF_BUDGET.md, guards | correctness-gate (re-gate), evolve-maintain |
| senior-review | any codebase | mentorship report, REVIEW_LEDGER.md | director + relevant lifecycle skill |
| scrutinize | a delta (plan/PR/diff/design doc) + host system | scrutiny report; REVIEW_LEDGER.md appends | director + the owning lifecycle skill per finding |
| evolve-maintain | incident/change + all ledgers | MAINT_LOG.md, strengthened invariants | build-discipline / problem-framing as classified |
| meta-skills | (always on) | discipline, not artifacts | every phase of every skill |

A skill whose required input artifact is missing does not improvise it: it either invokes the
producing skill or logs the gap as **(assumed)** with the cost of being wrong — chief-engineer
arbitrates which.

## 5. Verdict-line grammar and registry

Every skill run ends with exactly one machine-parseable verdict line. Shared shape:
`NOUN: state | state(qualifier) | escalated(to whom, why)`. Verdict lines are how a future model
reading a transcript or log knows where the lifecycle stopped. The registry — one noun per skill,
so a single grep (`^(LIFECYCLE|BRIEF|DESIGN|SLICE|WIRE|GATE|CAUSE|OPTIMIZE|REVIEW|SCRUTINY|MAINT):`)
recovers any run's trajectory:

| Noun | Owner | States |
|---|---|---|
| `LIFECYCLE` | chief-engineer | `<stage> \| next: <skill/director> \| blocked(missing: …)` |
| `BRIEF` | problem-framing | `ready \| blocked-on-questions \| revised(IDs)` |
| `DESIGN` | arch-design | `ready \| blocked-on-director(IDs) \| revised(IDs)` |
| `SLICE <name>` | build-discipline | `proven \| trace-only(reason) \| failed(at link/phase)` |
| `WIRE` | wire-check | `connected(tag) \| broken(link N: cause) \| blocked(environment)` |
| `GATE` | correctness-gate | `pass(tag) \| fail(behaviors, evidence)` |
| `CAUSE` | debug-protocol | `proven(cause) \| trace-only(reason) \| unreproduced` |
| `OPTIMIZE` | perf-optimize | `budgets-met \| improved(…) \| stopped(N) \| reverted(reason)` |
| `REVIEW` | senior-review | `shippable \| shippable-with-findings(top) \| not-shippable(blocker)` |
| `SCRUTINY` | scrutinize | `ship \| fix-then-ship(top) \| rework(reason) \| reject(reason) \| blocked(underspecified)` |
| `MAINT <ID>` | evolve-maintain | `resolved(class, tag) \| escalated(to) \| reverted` |

## 6. Degradation rule

Each skill carries a one-line gloss of the evidence tags so it survives being copied out of this
suite alone. If `PROTOCOL.md` is absent from the installation, the gloss governs; if present,
this file governs. A gloss is a pointer with a fallback, not a second authority.

The canonical gloss, copied verbatim so glosses cannot drift apart:

> (Gloss: **(proven)** executed · **(trace-only)** read, chain complete · **(suspected)** chain
> incomplete, flag only · **(assumed)** unverified premise — log it.)

The same pointer-with-fallback pattern applies to the decay rule (§1) and to any Law a skill
operationalizes: one short pointer line, never a second full statement. And skills never cite a
Law by bare number — always number **plus name** ("Law 3, violation ≠ deviation") so the reference
survives the skill being read standalone.

## 7. The scale rule (when ledgers become files)

The lifecycle always runs; ledger **files** materialize only when memory must outlive the session.
Write a ledger to disk when ANY of these holds:

(a) that ledger already exists in the project root — then it is authoritative and must be
maintained; (b) the work will span more than one session or more than one build slice; (c) the
director asks for it.

Otherwise the same content appears **inline in the report under the ledger's own heading** (a
three-line brief is still a brief) and is promoted to a file verbatim the moment (a) or (b)
becomes true. Creating nine ledger files for a thirty-line script is bureaucracy; running that
script's lifecycle entirely inline is not.

## 8. The fresh-eyes rule (separation of duties)

A model that built a change cannot review it as an outsider: its context is saturated with its
own reasoning, and self-review inherits self-blindness — the failure top-tier organizations
prevent by forbidding authors from approving their own pull requests. Therefore, when the stakes
warrant it (a one-way door, a ship declaration, or any `senior-review` / `scrutinize` run on work
this same session authored), the reviewing skill runs in a **fresh context** — a subagent in
Claude Code, a new session otherwise — given only the artifacts and the skill's contract file,
never the build conversation. This is Law 2 with teeth: the artifacts must suffice, and a fresh
reviewer who cannot operate from artifacts alone has found a Law 2 defect before reading a line
of code. Same-context review remains legal below that stakes bar, and the report then carries the
marker `(same-context review)` so the reader can weigh it accordingly.
