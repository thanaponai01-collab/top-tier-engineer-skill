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
  BRIEF.md      .md +          deferrals  (5 links     │   (REVIEW_      │
                DECISION                  per slice)   │   LEDGER.md)    │
                _LEDGER.md                the gate verdict      budgets + guards
        ▲                                                              │
        └────────────────── 6. evolve-maintain ◄───────────────────────┘
                            │        (the maintenance log; feeds incidents
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

`structure-gate` sits beside `wire-check` and `scrutinize` as a callable-any-stage service gate.
It answers **"measured
structural shape — is it spaghetti?"** with numbers, then routes every flag to
`senior-review`/`scrutinize` for the wisdom call; it never decides wisdom itself. Once a
codebase has accepted debt it also asks the question no point-in-time gate can — **"did it get
worse?"** — against a frozen baseline and `DEBT_LEDGER.md` (§8, the ratchet rule),
because debt is accrued by defensible increments and only accumulation is visible.

`latent-audit` is `symptom-audit`'s sibling for the *unfelt*: given no complaint at all, it
runs `tools/graph-audit.py` over the import/reference graph to find dead modules and unused
defs **(suspected — deletion only after a disconnection proof)** and layer-direction breaches
against the declared architecture **(proven)**; deletions land one scrutinized commit at a
time, never from the raw report.

`improvement-backlog` is the crossing where findings leave the suite's custody: any audit's
findings carried out to the project's issue tracker (or the report, when none exists) — one
issue per finding, with the tag, pin, cost, acceptance check and rank the *producing* skill
authored arriving intact — then picked back up one at a time through `chief-engineer`, each
issue closing only with verdict evidence. It authors no findings and re-ranks nothing; the half
nobody upstream can own is the close, which happens after every producer has closed
(DECISION_LEDGER D006, entered via a director field report per §9).

## Where the shared rules live

`PROTOCOL.md` — the evidence tags, the six rules, where things get written down, the handoff
chain (§4, which is the table this picture draws), the verdict grammar, the debt ratchet (§8), and
the plain-English report opening (§9). It is the only place these are stated; this map is a picture
of it, not a second copy. Isolated gate agents in `agents/` load it too — §1, §5 and §6 are all a
gate needs.

## Where the evidence lives

`runs/` — the run ledger: the suite executed against real systems (a Flask app, the Tier-Memory
system, itself, TickIt, an F1 telemetry app), plus `AUDIT_001`, an audit *of* those runs, and
`runs/patches/`, the fixes they delivered. `PROTOCOL.md` cites these by name as the provenance of
its rules — the pin rule (§1), the baseline rule (§1), and all of §7 were each earned by a specific
run, and a reader who cannot open the run cannot check the rule.

This directory is not supplementary — it is the evidence base for the suite's founding claim that
it finds real bugs and ships fixes, not just reports. It is published redacted (subjects are
SUBJECT_A/B/C, DECISION_LEDGER D004).
