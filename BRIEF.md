# The lazy path is the correct path

User request: design verify-loop from the point of view of the agent that uses it. Make it fit an
agent's habit of cutting things short, and split what makes a good answer out of SKILL.md so the
skill costs less per trigger without losing quality.

## How an agent actually uses a skill
- Reads SKILL.md once and rarely opens a reference unless an output line points at it.
- Runs the first command it is shown, follows what the output says, and stops at the first thing
  that looks like an answer.
- When a gate refuses without saying what would pass, reads the helper's source (eval
  `actions.txt`: `grep -n "def check_answer"` in two 1.18 runs).
- Copies whatever text it is handed: commands, lines, drafts.

## Decisions
- One command per question: `assess` (read-only), `advance` (make it proven), `status`.
- Quality knowledge lives where it fires, in three tiers by cost: SKILL.md routes (paid on every
  trigger); each verdict line carries its own meaning and remedy (paid only when it fires);
  references are lookups an output line links to.
- The helper drafts the answer from what it knows. `[[fill: ...]]` slots hold only judgment;
  `answer-check` refuses an unfilled slot, so copying the draft is the cheap path and still correct.
- Every refusal lists all problems at once, each with the line that fixes it.
- Everything an agent will paste runs as pasted (real helper path, same state option).
- Survey findings go into the answer contract (`gaps.survived`), not only into printed output.
- SKILL.md's size and its references to commands, links and verdicts are tested.

## Acceptance
`tests/test_agent_path.py`: one-call assess leaves the repo unchanged and finds a planted weak
check with or without `path:`; a filled draft passes `answer-check` and an unfilled one does not;
a refusal's `ADD THESE LINES` clear it; passing `advance` steps stay short and failing ones show why;
SKILL.md body ≤ 5,000 chars with no dead command, link, anchor or verdict name.

## Not in this slice
- Turn and cost budgets per eval case (`max_turns`, `max_cost`) and failing a try that reads the
  helper's source: needs fresh paid eval runs to set the numbers.
- An orientation header in `assess`/`advance` output for handoffs (`work/verify-loop-design.md` §4).
