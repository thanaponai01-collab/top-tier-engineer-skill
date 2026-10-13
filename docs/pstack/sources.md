# PStack comparison sources

Scope/status: [handoff](../../work/pstack-handoff.md). Source inspection: 2026-10-13.

## Official snapshot

Primary source: [Cursor PStack](https://github.com/cursor/plugins/tree/1dcc2bacde73ddd284803b7af28164d0436198fc/pstack).
The repository tree response identified `1dcc2bacde73ddd284803b7af28164d0436198fc`.
Sources below support mechanism descriptions, not claims of runtime reliability. The standalone
mirror README assisted discovery; the official snapshot owns upstream claims in this comparison.

| Source | Mechanism |
|---|---|
| [Poteto Mode](https://github.com/cursor/plugins/blob/1dcc2bacde73ddd284803b7af28164d0436198fc/pstack/skills/poteto-mode/SKILL.md) | Routing, roles, autonomy and sibling-plugin dependencies. |
| [Setup](https://github.com/cursor/plugins/blob/1dcc2bacde73ddd284803b7af28164d0436198fc/pstack/skills/setup-pstack/SKILL.md) | Available-model detection, role configuration and budgets. |
| [Verification generator](https://github.com/cursor/plugins/blob/1dcc2bacde73ddd284803b7af28164d0436198fc/pstack/skills/create-verification-skill/SKILL.md) | App interview, control recipe and one demonstrated journey. |
| [Verification maintenance](https://github.com/cursor/plugins/blob/1dcc2bacde73ddd284803b7af28164d0436198fc/pstack/skills/maintain-verification-skill/SKILL.md) | Source/live coverage, health rechecks and failure triage. |
| [Arena](https://github.com/cursor/plugins/blob/1dcc2bacde73ddd284803b7af28164d0436198fc/pstack/skills/arena/SKILL.md) | Isolated candidates, rubric, cross-judge and synthesis. |
| [Architect](https://github.com/cursor/plugins/blob/1dcc2bacde73ddd284803b7af28164d0436198fc/pstack/skills/architect/SKILL.md) | Distinct design sketches and implementation against a contract. |
| [Feature](https://github.com/cursor/plugins/blob/1dcc2bacde73ddd284803b7af28164d0436198fc/pstack/skills/poteto-mode/playbooks/feature.md) | Mandatory delegation and throughput checkpoint. |
| [Interrogate](https://github.com/cursor/plugins/blob/1dcc2bacde73ddd284803b7af28164d0436198fc/pstack/skills/interrogate/SKILL.md) | Model-diverse review and lead judgment. |
| [Correct](https://github.com/cursor/plugins/blob/1dcc2bacde73ddd284803b7af28164d0436198fc/pstack/skills/correct/SKILL.md) | Structural enforcement and rejection of a past mistake. |
| [Benchmark Checklist](https://github.com/cursor/plugins/blob/1dcc2bacde73ddd284803b7af28164d0436198fc/pstack/skills/benchmark-checklist/SKILL.md) | Tuning, useful work, noise, limits and relevance. |
| [Blast Radius](https://github.com/cursor/plugins/blob/1dcc2bacde73ddd284803b7af28164d0436198fc/pstack/skills/blast-radius/SKILL.md) | Indirect consumers and decisive safety facts. |
| [Shipping](https://github.com/cursor/plugins/blob/1dcc2bacde73ddd284803b7af28164d0436198fc/pstack/skills/poteto-mode/playbooks/shipping.md) | Independent verdicts, patch identity and stack landing. |
| [Eval](https://github.com/cursor/plugins/blob/1dcc2bacde73ddd284803b7af28164d0436198fc/pstack/skills/poteto-mode/playbooks/eval.md) | Blinding, organic tasks and transcript inspection. |
| [Reflect](https://github.com/cursor/plugins/blob/1dcc2bacde73ddd284803b7af28164d0436198fc/pstack/skills/reflect/SKILL.md) | Learning synthesis, skill-edit approval and backlog filing. |
| [Decision trail](https://github.com/cursor/plugins/blob/1dcc2bacde73ddd284803b7af28164d0436198fc/pstack/skills/show-me-your-work/SKILL.md) | Canonical log, evidence pointers and audit. |
| [Recall](https://github.com/cursor/plugins/blob/1dcc2bacde73ddd284803b7af28164d0436198fc/pstack/skills/recall/SKILL.md) | Scoped transcripts/shared records and live-state checks. |

How, Why, Figure It Out, Hillclimb and Benny sources supplied additional context; their workflows
were not executed. Orchestrate was inspected as an excerpt, not traced or executed in full.
Fleet/store adoption is deferred. No universal ranking of the plugins is established.

## Local authoritative records

- [BRIEF](../../BRIEF.md), [BUILD](../../BUILD.md), [rules](../../CLAUDE.md),
  [manifest](../../.claude-plugin/plugin.json): identity, decisions, scope and version.
- [Philosophy](../../PHILOSOPHY.md) and [catalog](../../CATALOG.md): habits and entry points.
- [Drive](../../skills/drive/SKILL.md), [routing](../../skills/drive/references/model-routing.md),
  [eval policy](../../skills/drive/references/evaluation-policy.md),
  [overnight](../../skills/drive-overnight/SKILL.md): authority, orchestration and recovery.
- [Verify Loop](../../skills/verify-loop/SKILL.md), [recipe](../../skills/verify-loop/references/project-recipe.md),
  [helper](../../skills/verify-loop/scripts/verify.py),
  [Correctness Gate](../../skills/correctness-gate/SKILL.md): proof requirements and selected enforcement.
- [Design](../../skills/arch-design/SKILL.md), [review](../../skills/scrutinize/SKILL.md),
  [performance](../../skills/perf-optimize/SKILL.md), [history](../../skills/code-history/SKILL.md): placement.
- [Foundation](../../skills/project-foundation/SKILL.md), [context](../../skills/project-context/SKILL.md),
  [memory](../../skills/project-context/references/memory.md): ownership and bounded retrieval.
- [Eval README](../../evals/README.md), [results](../../evals/RESULTS.md),
  [runner](../../evals/agent.py), [memory results](../../evals/PROJECT_MEMORY.md): evidence and limits.

## Historical corrections

The [2026-10-05 research](../../notes/pstack-verification-research.md) documents an older snapshot
and old verifier weaknesses. Current instructions/helper contain strict-verdict, failure-receipt
and content-signature protections. Old reproductions are historical findings, not proof the defects
still exist. No current reproduction was performed. The recall read-counter correction is recorded
with its exact action source in [validation](validation.md). Recheck sources after future changes.
