# The Top-Tier Engineer — Skill Map (v3)

Twelve skills wired into one engineer. A router reads the project's artifact state and dispatches
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
```

`scrutinize` sits beside `senior-review` as a parallel gate, invokable at any stage on any
not-yet-landed delta — plan, design doc, PR, or diff — answering "should this change exist, and
does it do what it claims?" before the change costs a build.

## The twelve, in one line each

| Skill | Question it owns |
|---|---|
| `chief-engineer` | Which stage are we in, and who runs next? |
| `problem-framing` | What are we actually building, falsifiably? |
| `arch-design` | How is it structured, and why — recorded reversibly? |
| `build-discipline` | Is every increment proven and wired before the next begins? |
| `wire-check` | Is it connected? |
| `correctness-gate` | Is it provably right? |
| `debug-protocol` | Why is it wrong? |
| `perf-optimize` | Is it measurably within budget, and guarded there? |
| `senior-review` | Is it wise? |
| `scrutinize` | Should this change exist, and does it do what it claims? |
| `evolve-maintain` | Does it stay healthy, and does every incident teach it? |
| `meta-skills` | Is the engineer itself behaving like one? |

## Where the shared rules live

`PROTOCOL.md` — evidence vocabulary, the six Laws, the ledger registry, the handoff chain, the
verdict-line grammar, and the degradation rule for skills copied out of the suite. Per Law 1 it is
the only place these are stated; this map is a picture of it, not a second copy.
