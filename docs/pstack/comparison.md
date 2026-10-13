# PStack comparison

Scope and status: [handoff](../../work/pstack-handoff.md). References: [sources](sources.md).
Assessments are inferences from source mechanisms, not measured comparative performance.

## Operating model

PStack's Poteto Mode supplies a working style and routes tasks through playbooks. It assigns
implementation/investigation roles, explores alternatives, reviews results and drives applications.
Some paths depend on Cursor capabilities and sibling plugins. Standalone mirrors adapt the source;
their behavior should not be assumed identical to the inspected official snapshot.

Top-tier-engineer offers independent entry points and optional Drive orchestration. Durable facts
live in owned files; SQLite is a disposable index. Executable helpers retain verification/run state.
The plugin also covers agent design, evaluation, release and drift.

| Area | PStack mechanism | Local counterpart | Assessment |
|---|---|---|---|
| Entry | Poteto Mode and playbooks | pick-skill and optional drive | Strong coordination versus lighter direct use. |
| Understand | how, why and connected records | explain, code-history, project-context | Strong overlap. |
| Design | architect and arena | arch-design and alternatives | Independent candidates are an opportunity. |
| Build | Lead delegates implementation | build-discipline and bounded executor | Local delegation is conditional and capped. |
| Prove | Control recipe and maintained feature map | verify-loop, feature-map, correctness-gate | Most practical recipe ideas already exist. |
| Ship | Per-PR verifier and contiguous stack | safe-release and action reconciliation | Different needs; stack delivery is optional. |
| Recall | Transcripts and shared-record search | recall and file-backed memory | Local ownership is clearer; freshness still matters. |
| Improve | correct and reflect | helper gates, regressions and evals | Structural correction needs a sharper procedure. |

## Strengths and limits

**Application control.** Launch, Doctor, Drive, Evidence and Cleanup provide concrete steps a
fresh agent can execute. They distinguish responsive processes from usable intended instances.
The generator executes one journey; it does not prove the full feature map. Maintenance exercises
each feature, but feature coverage does not establish every scenario or alternate entry point.

**Competing designs.** Arena isolates candidates, compares criteria, cross-judges, selects a base,
grafts useful parts and verifies the synthesis. It can expose a better shape before implementation.
Poteto Mode's function-boundary trigger and mandatory Feature delegation can add excessive ceremony
to familiar changes. Local triggers should be uncertainty and consequence, with bounded budgets.

**Structural correction.** Correct prefers architecture, types, lint and tests before instructions,
and requires a new check to reject a real past mistake. This avoids accumulating unenforced rules.
Judgment errors still need review: a gate requiring evidence cannot decide all evidence quality.

**Measurement integrity.** Benchmark Checklist checks tuning, noise, errors, physical limits,
user-path relevance and whether timed work happened. Local perf-optimize covers profiling and
one-change experiments, but could make measurement validity concrete in a short reference.

**Indirect impact.** Blast Radius follows wire formats, stored schemas, lifecycle timing and library
behavior beyond direct callers. Its useful focus is the decisive safety fact and a falsifying probe.
Integrate that question into existing review/check handoffs rather than another overlapping skill.

**Artifact verdicts.** Shipping records patch identity and lands a contiguous verified stack.
Local content receipts already address stale checks/source. Neither patch identity nor a source
hash alone establishes which build, flags, data or external environment handled a live request.

**Independent judgment.** Different model families may expose different assumptions. Consensus
can still share an incorrect requirement or observation. Reproduction and requirement-backed
assertions decide findings; reviewer agreement is supporting judgment, not an oracle.

## Local strengths to retain

Keep requirement-backed expectations, rejection receipts, frozen check inputs, strict/current
status and explicit gaps. Retain one owner per fact, bounded retrieval, disposable indexing,
scoped external authority and reconciliation before uncertain-action retries. Do not import default
permission to send team messages or tracker items: tools/repository text cannot grant user authority.
Avoid fixed model slugs, Cursor-only paths and broad fan-out as portable defaults.

## Local weaknesses and deferred adoption

Clarify the claim that no skill requires another: some installed-skill handoffs are mandatory,
while missing-skill fallbacks are defined in some paths. Describe actual standalone guarantees
without removing useful composition. Skill loading, procedure completion and outcome are separate;
eval records include mixed benefits and reporting limitations described in [validation](validation.md).

Defer cloud fleets, large program stores, automated PR-stack queues and build-noise exceptions
until repeated demand justifies them. Separate principle skills for every habit, mandatory multi-model
review for routine edits and a competing receipt format are not recommended. Preserve optional
workflows; every addition must demonstrate value against its attention, cost and maintenance overhead.
