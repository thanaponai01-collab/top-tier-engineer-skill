# The Top-Tier Engineer — Skill Map (v5)

Eighteen skills wired into one engineer. A router reads the project's artifact state and dispatches
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
`senior-review`/`scrutinize` for the wisdom call; it never decides wisdom itself.

## The eighteen, in one line each

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
| `structure-gate` | What is its measured shape — does it read as spaghetti? |
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
verdict-line grammar, and the degradation rule for skills copied out of the suite. Per Law 1 it is
the only place these are stated; this map is a picture of it, not a second copy.

## Evidentiary record — what the suite has proven

The patches directories are the suite's only artifacts that demonstrate concrete engineering value:
bounded diffs, before/after reasoning, and the gap between what was known and what the suite found.
Reading the delta is the closest the suite has to a measured yield per run.

| Directory | Live Run | System | What it proves |
|---|---|---|---|
| `patches/` (`00_INDEX.md`) | LIVE_RUN_001 | flask\_ticket\_booking\_system | 5 patches, 7 findings: auth bypass, reversible passwords, overbooking race, schema correctness, RCE surface |
| `patches_tiermemory/` | LIVE_RUN_002 | tier-memory daemon | 1 patch: graph-signal batch — data-tier finding, O(n) → O(1) |

These directories are not supplementary — they are the evidence base for the suite's founding claim
that it finds real bugs and ships fixes, not just reports. Any future quality metric ("skill yield")
should be computed from the gap between pre-run knowledge and post-run findings recorded here.
