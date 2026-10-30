<!-- Copy to BRIEF.md before building something new, or to work/briefs/<skill>.md before adding a
skill. Write each part as plain prose in your own words and replace every [[fill: ...]] slot. Keep
each marker (an HTML comment naming a term, such as end state) in front of the prose that covers
that term: markers are
hidden when the brief is rendered, and `python tools/spec_check.py <file>` reads them, not the
wording. It refuses a missing part, a term with no marker or no prose after it, an unfilled slot, a
stage without all three markers, evidence or verification with no `command` or file, and a named
test that does not exist. Terms: work/SPEC_TERMS.md. Constrain the outcome, not the process. -->
# [[fill: title, the idea in a few words]]

## Intent
<!-- purpose -->[[fill: why this exists, stated so the work can adapt when the plan breaks]]
<!-- end state -->[[fill: what the world looks like when this is done]]
<!-- done when -->[[fill: the explicit conditions that make the work complete]]

## Context
<!-- grounding -->[[fill: the facts that cannot be read from the repo and must be given]]
<!-- scope -->[[fill: what is in bounds]]
<!-- non-goals -->[[fill: what is explicitly out of bounds]]

## Guardrails
<!-- constraints -->[[fill: the limits on the solution, its requirements and prohibitions]]
<!-- invariants -->[[fill: what must stay true at every step, not just at the end]]
<!-- escalation -->[[fill: the decisions handed back to the user, or that there are none]]

## Freedom
<!-- latitude -->[[fill: the choices left to judgment, such as approach, order or tools]]

## Gates
<!-- precondition -->[[fill: a stage, and what is true before it starts]]
<!-- postcondition -->[[fill: what is true when it ends]]
<!-- evidence -->[[fill: the `command`, output or file that proves it]]
[[fill: the same three markers again for each further stage, or delete this slot]]

## Output
<!-- deliverable -->[[fill: the concrete thing handed back]]
<!-- acceptance -->[[fill: the checkable conditions, naming the tests/test_*.py that hold them]]
<!-- verification -->[[fill: the `command` that fails if it is not done]]
