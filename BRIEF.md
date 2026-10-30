# The lazy path is the correct path

## Intent
<!-- purpose -->This exists because verify-loop should be designed from the point of view of the
agent that uses it: it should fit an agent's habit of cutting things short, and what makes a good
answer should be split out of SKILL.md so the skill costs less per trigger without losing quality.
<!-- end state -->Copying what the helper hands over and following its output becomes the cheap
path, and it still ends in a correct, proven answer. <!-- done when -->The work is finished once
everything under Output is accepted.

## Context
<!-- grounding -->An agent uses a skill in a particular way. It reads SKILL.md once and rarely opens
a reference unless an output line points at it. It runs the first command it is shown, follows what
the output says, and stops at the first thing that looks like an answer. When a gate refuses
without saying what would pass, it reads the helper's source: in two 1.18 eval runs, `actions.txt`
shows `grep -n "def check_answer"`. And it copies whatever text it is handed, whether commands,
lines or drafts. <!-- scope -->This slice covers verify-loop's `assess`, `advance`, `status`,
`answer-check` and SKILL.md. <!-- non-goals -->It leaves out turn and cost budgets per eval case
(`max_turns`, `max_cost`) and failing a try that reads the helper's source, because setting those
numbers needs fresh paid eval runs. An orientation header in `assess` and `advance` output for
handoffs (`work/verify-loop-design.md` §4) was also left out of this slice; it was done afterwards,
as BUILD.md records under "Orientation comes first".

## Guardrails
<!-- constraints -->There is one command per question: `assess` (read-only), `advance` (make it
proven) and `status`. Quality knowledge lives where it fires, in three tiers by cost: SKILL.md
routes and is paid on every trigger, each verdict line carries its own meaning and remedy and is
paid only when it fires, and references are lookups an output line links to. The helper drafts the
answer from what it knows, with `[[fill: ...]]` slots holding only judgment, and `answer-check`
refuses an unfilled slot. Survey findings go into the answer contract (`gaps.survived`), not only
into printed output. The SKILL.md body stays within 5,000 characters, and its references to
commands, links and verdicts are tested. <!-- invariants -->At every step, `assess` leaves the repo
unchanged, every refusal lists all problems at once with the line that fixes each, and everything
an agent will paste runs as pasted, with the real helper path and the same state option.
<!-- escalation -->Nothing in this slice is handed back for a human call.

## Freedom
<!-- latitude -->How each helper drafts its answer and words its verdict lines, and the order of the
work, are left to judgment. Only the command contract above and the acceptance tests are fixed.

## Gates
<!-- precondition -->The rejection stage starts once the acceptance tests are written.
<!-- postcondition -->It ends when they fail on the current helpers, <!-- evidence -->shown by the
retained failing output named in BUILD.md. <!-- precondition -->Implementation starts once those
tests fail for the right reason. <!-- postcondition -->It ends when the focused tests pass,
<!-- evidence -->shown by `python -m unittest discover -s tests -p test_agent_path.py` reporting
`OK`. <!-- precondition -->The commit waits for the focused tests to pass.
<!-- postcondition -->It goes in once the full suite passes, <!-- evidence -->shown by
`python -m unittest discover tests` reporting `OK`, recorded in BUILD.md.

## Output
<!-- deliverable -->What comes back is the verify-loop helpers and SKILL.md, changed as above.
<!-- acceptance -->`tests/test_agent_path.py` holds it: a one-call assess leaves the repo unchanged
and finds a planted weak check with or without `path:`, a filled draft passes `answer-check` and an
unfilled one does not, a refusal's `ADD THESE LINES` clear it, passing `advance` steps stay short
and failing ones show why, and the SKILL.md body is at most 5,000 characters with no dead command,
link, anchor or verdict name. <!-- verification -->Running
`python -m unittest discover -s tests -p test_agent_path.py` proves it.
