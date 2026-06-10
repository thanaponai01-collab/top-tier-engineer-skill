# PROTOCOL.md — The Shared Layer

This file is the **single authoritative statement** of everything the eleven skills share.
Per Law 1 below, no skill restates what is written here; skills carry at most a one-line gloss
for graceful degradation (see §6). When a skill and this file appear to disagree, this file wins
and the disagreement is reported as a defect in the skill.

---

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
| evolve-maintain | incident/change + all ledgers | MAINT_LOG.md, strengthened invariants | build-discipline / problem-framing as classified |
| meta-skills | (always on) | discipline, not artifacts | every phase of every skill |

A skill whose required input artifact is missing does not improvise it: it either invokes the
producing skill or logs the gap as **(assumed)** with the cost of being wrong — chief-engineer
arbitrates which.

## 5. Verdict-line grammar

Every skill run ends with exactly one machine-parseable verdict line, defined in that skill.
Shared shape: `NOUN: state | state(qualifier) | escalated(to whom, why)`. Verdict lines are how a
future model reading a transcript or log knows where the lifecycle stopped.

## 6. Degradation rule

Each skill carries a one-line gloss of the evidence tags so it survives being copied out of this
suite alone. If `PROTOCOL.md` is absent from the installation, the gloss governs; if present,
this file governs. A gloss is a pointer with a fallback, not a second authority.
