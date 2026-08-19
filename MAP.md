# The Top-Tier Engineer — Skill Map

Twenty skills wired into one engineer. A router reads the project's artifact state and dispatches
every request to the right specialist; every specialist produces a **handoff artifact** the next
stage consumes — so any future model, with zero conversation history, resumes from artifacts alone.
The shared layer (vocabulary, laws, ledger registry, handoff chain) lives once, in `PROTOCOL.md`.

```
                          ┌──────────────────────────────┐
                          │        chief-engineer        │  ← every request enters here
                          │  reads ground → classifies → │
                          │     routes → one report      │
                          └──────────────┬───────────────┘
 ┌───────────────────────────────────────┼─────────────────────────────────────┐
 │                         meta-skills (always on)                             │
 │     calibration · tradeoffs · escalation · director-readability · drift     │
 └───────────────────────────────────────┼─────────────────────────────────────┘
                                         ▼
 1. problem-    2. arch-      3. build-          4. correctness-   5. perf-
    framing  →     design  →     discipline   →     gate        →    optimize
        │             │             │  └─ invokes      │   └─ parallel:  │
  PROBLEM_      ARCHITECTURE   commits +  wire-check   │   senior-review │
  BRIEF.md      .md +          TODO_      (5 links     │   (REVIEW_      │
  ASSUMPTIONS   DECISION       LEDGER.md  per slice)   │   LEDGER.md)    │
  .md           _LEDGER.md                CORRECTNESS_VERDICT.md   PERF_BUDGET.md
        ▲                                                              │
        └────────────────── 6. evolve-maintain ◄───────────────────────┘
                            │        (MAINT_LOG.md; feeds incidents
                            ▼         back into invariants)
                      debug-protocol
                  (unknown cause → proven Cause Verdict → back to evolve-maintain)

   symptom-audit ── felt complaint on an existing codebase → AUDIT_SPEC.md
   (symptom → trace → sweep → prescribe; phases execute via build-discipline,
    perf phases measured & guarded under perf-optimize)
```

`scrutinize` sits beside `senior-review` as a parallel gate, invokable at any stage on any
not-yet-landed delta — plan, design doc, PR, or diff — answering "should this change exist, and
does it do what it claims?" before the change costs a build.

`structure-gate` sits beside `wire-check` and `scrutinize` as a callable-any-stage service gate
— and the one that runs unattended in CI (`enforcement-floor`). It answers **"measured
structural shape — is it spaghetti?"** with numbers, then routes every flag to
`senior-review`/`scrutinize` for the wisdom call; it never decides wisdom itself. Once a
codebase has accepted debt it also asks the question no point-in-time gate can — **"did it get
worse?"** — against a frozen baseline and `DEBT_LEDGER.md` (PROTOCOL §10, the ratchet rule),
because debt is accrued by defensible increments and only accumulation is visible.

`latent-audit` is `symptom-audit`'s sibling for the *unfelt*: given no complaint at all, it
runs `tools/graph-audit.py` over the import/reference graph to find dead modules and unused
defs **(suspected — deletion only after a disconnection proof)** and layer-direction breaches
against the declared architecture **(proven)**; deletions land one scrutinized commit at a
time, never from the raw report.

`improvement-backlog` is the crossing where findings leave the suite's custody: any audit's
findings carried out to the project's issue tracker (or `BACKLOG.md` when none exists) — one
issue per finding, with the tag, pin, cost, acceptance check and rank the *producing* skill
authored arriving intact — then picked back up one at a time through `chief-engineer`, each
issue closing only with verdict evidence. It authors no findings and re-ranks nothing; the half
nobody upstream can own is the close, which happens after every producer has closed
(DECISION_LEDGER D006, entered via a director field report per PROTOCOL §12).

## The twenty, in one line each

| Skill | Question it owns |
|---|---|
| `chief-engineer` | Which stage are we in, and who runs next? |
| `problem-framing` | What are we actually building, falsifiably? |
| `arch-design` | How is it structured, and why — recorded reversibly? |
| `build-discipline` | Is every increment proven and wired before the next begins? |
| `wire-check` | Is it connected? |
| `correctness-gate` | Is it provably right? |
| `debug-protocol` | Why is it wrong? |
| `symptom-audit` | Where does the felt complaint live, and what's the cheapest path to relief? |
| `perf-optimize` | Is it measurably within budget, and guarded there? |
| `data-tier` | Does this query scale better than the data grows? |
| `threat-model` | What can an adversary make it do that it must not? |
| `senior-review` | Is it wise? |
| `scrutinize` | Should this change exist, and does it do what it claims? |
| `structure-gate` | What is its measured shape — does it read as spaghetti, and did it get worse? |
| `latent-audit` | What is provably dead, mislayered, or dormantly broken — with no symptom to guide the search? |
| `improvement-backlog` | Did the finding survive the crossing into a tracker intact, and did the close carry evidence? |
| `data-evolution` | How does stored data change shape without loss, reversibly? |
| `ship-gate` | Is releasing it reversible, observable, and bounded? |
| `evolve-maintain` | Does it stay healthy, and does every incident teach it? |
| `meta-skills` | Is the engineer itself behaving like one? |

> The three skills added in v1.5.0 (`threat-model`, `ship-gate`, `data-evolution`) each closed a
> mandate gap exposed by the first real run (LIVE_RUN_001): security findings with no pipeline, the
> unowned act of shipping, and data-shape change whose rollback semantics differ from code's. The
> `tools/verdict-lint.py` validator added the suite's first mechanical enforcement.

## Where the shared rules live

`PROTOCOL.md` — evidence vocabulary, the six Laws, the ledger registry, the handoff chain, the
verdict-line grammar, the degradation rule for skills copied out of the suite, the debt ratchet
(§10), and the sense floor (§11) that checks a finished run against the director's own words. Per
Law 1 it is the only place these are stated; this map is a picture of it, not a second copy.

`PROTOCOL.md` states rules and nothing else. **Why** each rule exists — the failure that earned it,
its provenance, the argument — lives in `PROTOCOL_RATIONALE.md`, which no run loads and which is
read only when a rule is being questioned, amended, or removed. That split is Law 1 applied to the
suite's own doctrine, and it is also §11's terse rule at the source: prose a run reads is prose a
run imitates.

`GATE_DOCTRINE.md` is the third doctrine file: the scoped subset an isolated §8.2 gate agent loads
*instead of* `PROTOCOL.md`. A gate does not route, build, or own ledgers, so it needs the evidence
vocabulary and the verdict grammar and nothing else — and because §8.2 gates run in parallel
isolated contexts, each one that loaded full doctrine multiplied the session's largest fixed cost by
the number of gates. `tools/doctrine-budget.py` prints the per-gate figure on every run.

## Where the evidence lives

`runs/` — the run ledger. `LIVE_RUN_001`–`004` are the suite executed against real systems
(a Flask app, the Tier-Memory system, itself, and TickIt); `LIVE_RUN_005` is the first run under
the PROTOCOL §12 cadence obligation, against an independent F1 telemetry app that had already been
touched by an earlier, un-logged copy of the suite; `AUDIT_001` is an audit *of* those runs;
`runs/patches/` holds the fixes those runs delivered. `PROTOCOL.md` cites these files by name as
the provenance of its rules — the pin rule (§1), the baseline rule (§1), and all of §9 were each
*earned* by a specific run, and a reader who cannot open the run cannot check the rule.

This directory is not supplementary — it is the evidence base for the suite's founding claim
that it finds real bugs and ships fixes, not just reports. **Skill-yield, computed for the first
time in `LIVE_RUN_005`:** the gap between pre-run knowledge (a subject's existing docs/ledgers) and
post-run findings (proven, run-earned) — LIVE_RUN_005 yielded one proven defect (a debt-ratchet
regression the subject's own baseline had already silently missed for one commit), one confirmed
cross-codebase pattern (independently reproducing IMPROVEMENT_PLAN.md's F4 on a second codebase),
and one boundary shape checked clean (Discord OAuth + tier gate, threat-model's first bind against
a session-cookie + third-party-IdP trust boundary rather than LIVE_RUN_004's RLS boundary). It is
kept separate from the skill surface an installer reads, but it **ships**: from v1.14.0 to v1.16.1
it was in `.gitignore`, which made every "earned by `AUDIT_001`" citation in `PROTOCOL.md` a dead
link and left the two CI gates that lint transcripts pointed at an empty path (v1.17.0 fixed both).
