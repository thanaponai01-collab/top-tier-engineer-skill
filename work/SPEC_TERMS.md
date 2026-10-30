# Spec terms

The words behind `work/SPEC_TEMPLATE.md`. Principle: constrain the outcome, not the process.

> Give the work **intent**, **constraints** and **latitude**; gate each stage on
> **postconditions** backed by **evidence**; accept the result against **acceptance criteria**.

## The whole approach
| Term | Definition |
|---|---|
| Declarative specification | Describing what must be true, not how to get there. |
| Outcome-based prompting | Giving the result and the acceptance criteria and leaving the method open. |
| Scaffolded autonomy | A fixed structure with free judgment inside it. |
| Mission command (*Auftragstaktik*) | Give intent and limits, and trust the executor to decide the method. |

## Template parts
Each part is plain prose in any wording; a hidden marker in front of the prose names the term it covers, and `tools/spec_check.py` reads the markers.

| Part | Marker | Term | Definition |
|---|---|---|---|
| Intent | `<!-- purpose -->` | Commander's intent | The purpose and end state, stated so the executor can adapt when plans break. |
| Intent | `<!-- end state -->` | End state | What the world looks like when the task is done. |
| Intent | `<!-- done when -->` | Definition of done | The explicit conditions that make the work complete. |
| Context | `<!-- grounding -->` | Grounding | Facts that cannot be inferred and must be given. |
| Context | `<!-- scope -->` | Scope | What is in bounds. |
| Context | `<!-- non-goals -->` | Non-goals | What is explicitly out of bounds. |
| Guardrails | `<!-- constraints -->` | Constraint | A limit on the solution space: a requirement or a prohibition. |
| Guardrails | `<!-- invariants -->` | Invariant | Something that must stay true throughout, not just at the end. |
| Guardrails | `<!-- escalation -->` | Escalation point | A decision handed back to a human. |
| Freedom | `<!-- latitude -->` | Latitude, discretion, degrees of freedom | The room to decide, permission to use judgment, and the specific choices left open. |
| Gates | all three, per stage | Quality gate, exit criteria | A checkpoint work cannot pass without meeting its criteria. |
| Gates | `<!-- precondition -->` | Precondition | What must be true before a step starts. |
| Gates | `<!-- postcondition -->` | Postcondition | What must be true when a step ends (design by contract). |
| Gates | `<!-- evidence -->` | Evidence | The concrete proof a gate was met: test output, diff or artifact. |
| Output | `<!-- deliverable -->` | Deliverable | The concrete thing handed back. |
| Output | `<!-- acceptance -->` | Acceptance criteria | Checkable conditions the deliverable must meet. |
| Output | `<!-- verification -->` | Verification | Proving it works, not just claiming it does. |
