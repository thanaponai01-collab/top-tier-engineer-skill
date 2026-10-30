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

## Template fields
| Section | Field | Term | Definition |
|---|---|---|---|
| 1. Intent | Purpose | Commander's intent | The purpose and end state, stated so the executor can adapt when plans break. |
| 1. Intent | End state | End state | What the world looks like when the task is done. |
| 1. Intent | Done when | Definition of done | The explicit conditions that make the work complete. |
| 2. Context | Grounding | Grounding | Facts that cannot be inferred and must be given. |
| 2. Context | Scope | Scope | What is in bounds. |
| 2. Context | Non-goals | Non-goals | What is explicitly out of bounds. |
| 3. Guardrails | Constraints | Constraint | A limit on the solution space: a requirement or a prohibition. |
| 3. Guardrails | Invariants | Invariant | Something that must stay true throughout, not just at the end. |
| 3. Guardrails | Escalate | Escalation point | A decision handed back to a human. |
| 4. Freedom | Open choices | Latitude, discretion, degrees of freedom | The room to decide, permission to use judgment, and the specific choices left open. |
| 5. Gates | Stage | Quality gate, exit criteria | A checkpoint work cannot pass without meeting its criteria. |
| 5. Gates | Precondition | Precondition | What must be true before a step starts. |
| 5. Gates | Postcondition | Postcondition | What must be true when a step ends (design by contract). |
| 5. Gates | Evidence | Evidence | The concrete proof a gate was met: test output, diff or artifact. |
| 6. Output | Deliverable | Deliverable | The concrete thing handed back. |
| 6. Output | Acceptance | Acceptance criteria | Checkable conditions the deliverable must meet. |
| 6. Output | Verification | Verification | Proving it works, not just claiming it does. |
