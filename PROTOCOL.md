# PROTOCOL.md — The Shared Layer

This file is the **single authoritative statement** of everything the eighteen skills share.
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
   better results. *Acceptance criterion (so this Law is falsifiable like any other):* a skill
   conforms only if its body contains no hard-coded answer, stack name, threshold, or finding that
   a future model would have to override to do better — every such particular is a worked example
   labelled as illustrative, never the contract. The test is the **substitution test**: replace
   every concrete instance in the skill with the phase or rule it illustrates; if the skill still
   fully specifies the work, it constrains process; if removing the instances leaves a hole, that
   instance was load-bearing knowledge and is a Law 6 violation. The thesis that a stronger model
   *actually* does better through the same contract is, suite-wide, **(suspected)** until a
   two-tier run measures it (the experiment is specified in `LIVE_RUN_003.md`); per-skill
   conformance to the substitution test is **(trace-only)** and checkable by reading.

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
| `DATA_TIER.md` | data-tier | Access → cost-class → plan-evidence → verdict, per data-access change |
| `AUDIT_SPEC.md` | symptom-audit | Pinned symptom, cause→location→cost table, phased prescription, pre-written checks |
| `REVIEW_LEDGER.md` | senior-review | Unresolved novelty: hypothesis + the experiment that would settle it |
| `THREAT_MODEL.md` | threat-model | Assets, trust boundaries, abuse cases, evidence tag, defense status |
| `RELEASE_PLAN.md` | ship-gate | Rollout strategy, reversibility class, rollback steps, watch signals, go/no-go |
| `MIGRATION_PLAN.md` | data-evolution | Forward + backward paths, point-of-no-return, verification evidence, cutover |
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
| symptom-audit | existing codebase + a felt complaint | AUDIT_SPEC.md (diagnosis + phased prescription) | build-discipline (execute phases); perf-optimize (measure & guard perf phases); debug-protocol / wire-check on reroute |
| perf-optimize | a passed gate + a budget | PERF_BUDGET.md, guards | correctness-gate (re-gate), evolve-maintain |
| data-tier | a data-access change + its schema | DATA_TIER.md + corrected query/index | perf-optimize (wall-clock budget); data-evolution (index migration); arch-design (data-model flaw) |
| senior-review | any codebase | mentorship report, REVIEW_LEDGER.md | director + relevant lifecycle skill |
| threat-model | a system/design + its trust boundaries | THREAT_MODEL.md + abuse-case test specs | correctness-gate (run the tests); arch-design (trust-placement); ship-gate (clearance) |
| ship-gate | a gated (and threat-cleared) change + deploy target | RELEASE_PLAN.md, go/no-go | data-evolution (if migration); evolve-maintain (post-release) |
| data-evolution | a structural data change + existing data | MIGRATION_PLAN.md + migration/rollback code | build-discipline + correctness-gate (execute); ship-gate (carry down-path) |
| scrutinize | a delta (plan/PR/diff/design doc) + host system | scrutiny report; REVIEW_LEDGER.md appends | director + the owning lifecycle skill per finding |
| structure-gate | a codebase or a slice's changed files | STRUCTURE_REPORT.md + structural report | senior-review / scrutinize (wisdom call on each flag); arch-design (cycle ⇒ layering error, god-file ⇒ missing boundary) |
| evolve-maintain | incident/change + all ledgers | MAINT_LOG.md, strengthened invariants | build-discipline / problem-framing as classified |
| meta-skills | (always on) | discipline, not artifacts | every phase of every skill |

A skill whose required input artifact is missing does not improvise it: it either invokes the
producing skill or logs the gap as **(assumed)** with the cost of being wrong — chief-engineer
arbitrates which.

**Concurrent invocation sequencing (v1.7.0).** Two boundary pairs have ordering ambiguity when
both fire on the same artifact in the same run:

- **`data-tier` + `perf-optimize`**: when a data-access change warrants both a `DATATIER` finding
  and a `PERF_BUDGET.md` wall-clock entry, `data-tier` closes first (`DATATIER` verdict), then its
  findings arrive as perf-optimize Phase-4 hypotheses. The `DATATIER` verdict appears before
  `OPTIMIZE` in the transcript; `verdict-lint.py` interprets any `DATATIER` before `OPTIMIZE` as
  correct ordering.

- **`evolve-maintain` → `data-evolution`**: when evolve-maintain classifies an intervention as
  `Migrate` and invokes `data-evolution`, evolve-maintain closes immediately with its `MAINT`
  verdict; `data-evolution` then runs as a peer and produces its `MIGRATE` verdict afterward. The
  `MAINT` verdict appears before `MIGRATE` in the transcript. evolve-maintain does not hold its
  verdict open waiting for data-evolution.

## 5. Verdict-line grammar and registry

Every skill run ends with exactly one machine-parseable verdict line. Shared shape:
`NOUN: state | state(qualifier) | escalated(to whom, why)`. Verdict lines are how a future model
reading a transcript or log knows where the lifecycle stopped. The registry — one noun per skill,
so a single grep (`^(LIFECYCLE|BRIEF|DESIGN|SLICE|WIRE|GATE|CAUSE|AUDIT|OPTIMIZE|DATATIER|REVIEW|SCRUTINY|STRUCTURE|THREAT|SHIP|MIGRATE|MAINT)( [^:]+)?:`)
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
| `AUDIT` | symptom-audit | `prescribed(N phases, top: …) \| clean(traced path healthy) \| rerouted(to skill: reason) \| blocked(symptom unpinnable)` |
| `OPTIMIZE` | perf-optimize | `budgets-met \| improved(…) \| stopped(N) \| reverted(reason)` |
| `DATATIER` | data-tier | `clean(N bounded) \| findings(top: …, class: O(…)) \| blocked(no plan: …)` |
| `REVIEW` | senior-review | `shippable \| shippable-with-findings(top) \| not-shippable(blocker)` |
| `THREAT` | threat-model | `clear(N modelled, M defended) \| findings(top: …) \| blocked(boundary unmappable: …)` |
| `SHIP` | ship-gate | `go(strategy, rollback tag) \| stage(canary plan) \| hold(blocker) \| escalated(one-way door: …)` |
| `MIGRATE` | data-evolution | `planned(reversible) \| planned(lossy-after-step-N) \| verified(copy) \| blocked(no safe backward path)` |
| `SCRUTINY` | scrutinize | `ship \| fix-then-ship(top) \| rework(reason) \| reject(reason) \| blocked(underspecified)` |
| `STRUCTURE` | structure-gate | `clean(N files, M functions) \| findings(top: <signal>, count: K) \| blocked(no analyzable source)` |
| `MAINT <ID>` | evolve-maintain | `resolved(class, tag) \| escalated(to) \| reverted` |

**Tool-output nouns.** Some verdict nouns are emitted by suite *tools*, not skills, and so own no row
in the skill registry above: `TRACE` (run-trace.py). Tool nouns are linted for form like any other
but are not part of the §4 skill handoff chain. (Note: `STRUCTURE` is emitted by the tool
`structure-report.py` *and* owned by the skill `structure-gate`, so it keeps its row above.)

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

**What the gloss must carry (the extraction floor).** A skill read alone — `skills/<name>/SKILL.md`
with no `PROTOCOL.md` beside it — is a real deployment, not an error: skills get copied into other
suites, pasted into prompts, vendored one-file. Before this version the gloss carried only the four
evidence tags, so an extracted skill kept its tags and silently lost every Law, the ledger registry,
and the verdict grammar — it operated lawless except for vocabulary. The fix is the **name-plus-clause
rule**: because every Law is always cited by number *and* a ≤6-word naming clause (the rule above),
the citation itself is the fallback. "Law 1, every rule lives in exactly one place" survives
extraction whole; "Law 1" alone does not. A skill is therefore conformant only if every Law it relies
on is cited name-and-clause at least once in its own body, so a reader with no `PROTOCOL.md` can
recover the rule's content — not just its number — from the skill alone. The verdict line is its own
fallback by construction: §5's grammar is restated by every skill's final-line example. This is the
degradation floor: tags + named Laws + a verdict example, all carried in-skill, so extraction costs a
skill its cross-references but never its constitution.

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

**§8.1 — Structural separation for review-class skills (harness obligation).**
When `senior-review`, `scrutinize`, or `structure-gate` is run on work authored in the same
session, the fresh-eyes requirement is satisfied **only** by one of: (a) a *separate invocation
with no shared build context* — the reviewer is given the artifacts and the diff, not the build
conversation; or (b) the mechanical gate (`enforcement-floor` CI), which is context-free by
construction and therefore always counts as an independent reviewer for the structural and
verdict-form dimensions it covers. The `(same-context review)` marker remains legal **only**
when neither (a) nor (b) is available, and a run that used the marker where (b) was available is
a defect: the CI gate was the independent reviewer and should have been cited. In short: *prefer
a structural separation you cannot fake over a marker you can.*
