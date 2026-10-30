<!-- Copy to BRIEF.md before building something new, or to work/briefs/<skill>.md before adding a
skill. Replace every [[fill: ...]] slot; `python tools/spec_check.py <file>` refuses a missing
section, an empty field, an unfilled slot, a gate without evidence, and a named test that does not
exist. Terms: work/SPEC_TERMS.md. Constrain the outcome, not the process. -->
# [[fill: title, the idea in a few words]]

## 1. Intent
- Purpose: [[fill: why this exists, stated so the work can adapt when the plan breaks]]
- End state: [[fill: what the world looks like when this is done]]
- Done when: [[fill: the explicit conditions that make the work complete]]

## 2. Context
- Grounding: [[fill: facts that cannot be inferred from the repo and must be given]]
- Scope: [[fill: what is in bounds]]
- Non-goals: [[fill: what is explicitly out of bounds]]

## 3. Guardrails
- Constraints: [[fill: limits on the solution, requirements and prohibitions]]
- Invariants: [[fill: what must stay true throughout, not just at the end]]
- Escalate: [[fill: decisions handed back to the user, or none]]

## 4. Freedom
- Open choices: [[fill: the choices left to judgment, such as approach, order or tools]]

## 5. Gates
| Stage | Precondition | Postcondition | Evidence |
|---|---|---|---|
| [[fill: stage]] | [[fill: true before it starts]] | [[fill: true when it ends]] | [[fill: test output, diff or file that proves it]] |

## 6. Output
- Deliverable: [[fill: the concrete thing handed back]]
- Acceptance: [[fill: checkable conditions, naming the tests/test_*.py that hold them]]
- Verification: [[fill: the `command` that fails if it is not done]]
