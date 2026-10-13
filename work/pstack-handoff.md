<!-- context-id: task:pstack-adoption -->
<!-- context-type: task -->
<!-- context-area: plugin-improvement -->
<!-- context-status: active -->
<!-- context-paths: skills/drive, skills/verify-loop, skills/arch-design, skills/perf-optimize, skills/scrutinize, evals -->
# PStack comparison and improvement handoff

Updated: 2026-10-13, Asia/Bangkok. Overall status: **P01-P03 implemented with bounded trials; P04 implemented with partial behavior evidence; P05 implemented with one bounded behavior trial and repository gates passed; P06 implemented with one bounded behavior trial and decisive-boundary probe (procedure validation partial); P07-P08 proposed or awaiting validation; P09 deferred**.

Borrow PStack mechanisms that improve observed outcomes while retaining top-tier-engineer's
evidence controller, bounded project memory and scoped user authority. This handoff records
comparison, scope and adoption status; it does not grant authority by itself. The user's current
`/drive implement p05` request authorizes local implementation and bounded evaluation, not a release.
The earlier request was discussion only; the subsequent request authorized this document.
The later `/drive implement the p01` request authorizes P01 implementation and its bounded trials.
The subsequent `/drive implement the p02` request authorizes P02 implementation and local application trials.

The subsequent `/drive implement the p03` request authorizes P03 local implementation and bounded trials.
P04 local implementation/trials authorized by the subsequent `/drive implement the p04` request.
P05 local implementation/trial authorized by the current `/drive implement p05` request.
P06 local implementation/trial authorized by the current `/drive implement the p06` request.
## Current state

- Compared official Cursor PStack at `1dcc2bacde73ddd284803b7af28164d0436198fc` with local
  top-tier-engineer 4.61.1, including existing uncommitted work.
- The user called the source plugin Carousel. Cursor PStack is the working interpretation
  supported by source discovery; the user has not explicitly confirmed the name.
- Inspected instructions, selected helpers and local evaluation records. No PStack execution,
  head-to-head behavior experiment or comparative cost/latency measurement was performed.
- Many verification mechanisms already exist locally. Presence does not prove agent compliance
  or successful operation across browser, API, CLI and desktop application surfaces.
- Preserve the broader project Next in [BUILD.md](../BUILD.md); this proposal does not replace it.

## Status meanings

| Status | Meaning |
|---|---|
| Research complete | Relevant source inspected; comparative superiority remains unmeasured. |
| Existing; validation needed | Local mechanism exists; its named acceptance trials remain. |
| Proposed | Recommendation only; implementation has not started. |
| Deferred | Conditional future work, outside initial adoption. |
| Verified | Executed acceptance check with current retained evidence. |
| Blocked | An attempted authorized task cannot continue; name dependency and next action. |

## Adoption status

This table owns adoption status. Linked sections own rationale, scope and acceptance checks.

| ID | Workstream | Priority | Status | Detail |
|---|---|---|---|---|
| P01 | Isolated behavior trials and trustworthy reporting | First | Verified (bounded recall pilot) | [Evidence](p01/evidence.md) |
| P02 | App launch, doctor, real drive and evidence cleanup | First | Verified (bounded API, CLI and browser trials) | [Evidence](p02/evidence.md) |
| P03 | Enforce recurring mistakes structurally | Second | Verified (bounded subprocess enforcement) | [Evidence](p03/evidence.md) |
| P04 | Benchmark validity and measured work counts | Second | Implemented; procedure validation partial | [Evidence](p04/evidence.md) |
| P05 | Optional competing designs | Third | Verified (one bounded live replay per fixture; reliability unmeasured) | [Evidence](p05/evidence.md) |
| P06 | Test decisive safety assumptions | Third | Implemented; bounded trial passed; procedure validation partial | [Evidence](p06/evidence.md) |
| P07 | Identify the actual running artifact | Second | Existing; validation needed | [Plan](../docs/pstack/adoption-plan.md) |
| P08 | Clarify standalone use and skill handoffs | Second | Proposed | [Comparison](../docs/pstack/comparison.md) |
| P09 | Stack delivery and large agent programs | Later | Deferred | [Comparison](../docs/pstack/comparison.md) |

## Next for this proposal

P01's loading fix and repeated recall pilot are retained in [evidence](p01/evidence.md).
Next expansion requires a fixture with independently observed full procedure compliance;
the current recall case cannot establish that. Broader fresh-reader/recovery reliability remains open.
Do not launch a full matrix, add skills or alter release machinery before locating a demonstrated gap.

## Detailed handoff

- [Comparison](../docs/pstack/comparison.md): strengths, weaknesses, overlap and deferred ideas.
- [Adoption plan](../docs/pstack/adoption-plan.md): bounded slices and acceptance criteria.
- [Validation](../docs/pstack/validation.md): trials, evidence, reporting and resume rules.
- [Sources](../docs/pstack/sources.md): pinned source links and historical corrections.
- Background: [older verification research](../notes/pstack-verification-research.md).

## Status maintenance

After authorized work, update the affected row and link acceptance evidence from its detail section.
Keep failed and inconclusive results. A skill change needs actual behavioral replay; helper tests
alone cannot mark it verified. RUN.json remains authoritative for driven execution, while this
handoff owns proposal status. Recheck current files before resuming concurrent or interrupted work.
