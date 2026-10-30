# Mistake proof: make a repeated agent mistake impossible

## Intent
<!-- purpose -->Agents in a repo keep making the same mistakes, and the usual fix is a new line in
CLAUDE.md that the next agent never reads, so nothing fails when it is skipped. The plugin's own
rule is mechanics, not advice. Give an agent a helper that turns a repeated mistake into a check
that fails: it groups past mistakes into classes, asks for the strongest fix that works
(architecture, then types, then a lint, then a test, docs last), and will not accept a check
until it has run red on the commit where the mistake happened and green on the fix. Adapted from
pstack's prose `correct` skill (cursor/plugins, `pstack/skills/correct/SKILL.md`); its fix order
and rule table become stages and a table the helper checks, not steps the agent promises to do.
<!-- end state -->`python plugin/skills/mistake-proof/scripts/mistake.py <repo> --mine` lists candidate
mistakes from the repo's history; `--gate` refuses until each class has two pieces of evidence,
a level with a reason why each stronger level did not work, and a check that fails on a real
past mistake and passes on the fix; the target repo's agent instruction file holds a rule table
in which every row names an enforcer that exists, and a rule with nothing enforcing it is
reported as a repeat.
<!-- done when -->Every condition under Acceptance passes, the skill is registered like its
siblings, and the full suite passes.

## Context
<!-- grounding -->
- The plugin's rule: mechanics, not advice. A rule that only lives in prose reads the same
  whether or not anyone follows it, so only a check the helper saw fail counts as enforcement.
- No sibling covers this. structure-gate measures complexity, debug-protocol finds the cause of
  one failure, latent-audit proves code dead, verify-loop proves one change. None asks which
  mistake keeps coming back, or whether the rule written against it can fail.
- Where mistakes show up without a chat log: `Revert "…"` commits, commits that change the same
  lines back, fix commits that name an earlier one, review comments in merged PR text, and
  workaround comments (`# don't …`, `# must …`, `NOTE:`) next to code. The operator's correction
  in chat is evidence too, but only the agent sees it, so it is recorded with `--add`.
- A class counts once it has happened twice. One occurrence is a bug for debug-protocol, not a
  pattern.
- The fix levels in order: 1 architecture (one owner, one supported way, the wrong import fails,
  old ways deleted), 2 types (the bad state cannot be written), 3 a lint or CI check whose error
  names the right file, type or function, 4 a test of behaviour, 5 docs or agent rules, only for
  judgment calls. A lower level needs a reason why each higher one did not work.
- Agents copy the nearest example. If the bad pattern is already common, a check that fails on
  every old use will be switched off; it fails only on what a change adds.
<!-- scope -->A new manual-only skill `plugin/skills/mistake-proof/` (SKILL.md, `scripts/mistake.py`,
`scripts/_encoding.py`, stdlib only), state in `.mistakes/`; git history and tracked text files
of the target repo; `tests/test_mistake.py`; registration in CLAUDE.md, both plugin manifests'
version and CHANGELOG.md; `.mistakes/` added to the other helpers' skip lists.
<!-- non-goals -->
- Writing the checks itself: the agent writes the lint, type or test; the helper only judges
  whether it can fail.
- Reading chat history or other agent transcripts; corrections come in through `--add`.
- Calling GitHub or any network service for review comments; only what is in the local clone.
- A linter framework or rule language: a check is any command that exits non-zero.
- Large deletions of an old API: when a level-1 fix removes something with live callers, the
  helper points at evolve-maintain and does not plan the migration.

## Guardrails
<!-- constraints -->
- One helper `M` = `python <skill>/scripts/mistake.py <repo>`: `M --mine [--since REF]` lists
  candidates and drafts `.mistakes/classes.md`; `M --add "<what the operator corrected>"`
  records a correction with its date; `M --gate` checks every stage and the rule table;
  `M --answer-check FILE` refuses a reply that claims more than the gate saw.
- Each class in `.mistakes/classes.md` has a name, at least two evidence lines (a commit sha that
  exists, a `file:line` that exists, or an `--add` entry), a level from 1 to 5, and a
  `why not <level>` line for every stronger level.
- Each class at levels 1 to 4 names its proof: a check command and the past commit where the
  mistake is present. The helper runs the command in a scratch worktree of that commit with the
  check applied (must fail) and on the working tree (must pass). A check that passes on the past
  mistake is refused as one that cannot fail. A level-5 class has no proof and is listed as
  unenforced in every reply.
- A check that fails on the current tree because the pattern is already common is refused, with
  the hint to fail only on added lines.
- If the repo has CI config (`.github/workflows/`, `.gitlab-ci.yml` and the like), each check
  command must appear in it; with no CI the reply says so.
- The rule table sits between two `mistake-rules` HTML-comment markers in the target repo's agent
  instruction file (CLAUDE.md, AGENTS.md or `.cursor/rules/`), one row per class: rule, level,
  enforcer. The gate refuses a row whose enforcer path or command does not exist, and reports
  as a repeat a class with new evidence dated after its row was added while its enforcer is
  still level 5.
- An exception is a comment on the offending line: `mistake-ok: <class> reason=… expires=YYYY-MM-DD
  approved=<name>`. The gate refuses one with a field missing or a date passed.
- SKILL.md body ≤ 5,000 chars, shaped like blast-radius's (goal, `M`, stages table).
<!-- invariants -->
- The helper never writes the product tree: proofs run in scratch worktrees; only `.mistakes/`
  changes. The agent's own fixes are ordinary edits, outside the helper.
- Every refusal lists all problems at once, each with the line or command that fixes it.
- `.mistakes/` is skipped by the other helpers, and `.verify-state`, `.wire`, `.features`,
  `.release`, `.evolve`, `.perf`, `.blast` are skipped by this one.
<!-- escalation -->Every exception needs a human's name in `approved=`; the agent never fills it.
Whether a reported repeat should also block safe-release's gate is a cross-skill decision for the
user; this slice only reports.

## Freedom
<!-- latitude -->How candidates are mined and grouped, how a commit's date is compared with a
row's (blame, log or a stored date), how the check is applied to the past commit (cherry-pick,
copying the check files, or a patch), the wording of drafts and refusals, and the order of
work. Only the command contract, the classes and table formats, the exception format, the
red-on-past green-on-now rule and the Acceptance tests are fixed.

## Gates
<!-- precondition -->Rejection before implementation starts once `tests/test_mistake.py` is
written. <!-- postcondition -->It ends when it fails because `mistake.py` does not exist or does
not catch each plant, <!-- evidence -->shown by the retained failing output, named in BUILD.md.
<!-- precondition -->Implementation starts once the tests fail for the right reason.
<!-- postcondition -->It ends when the focused tests pass, <!-- evidence -->shown by
`python -m unittest discover -s tests -p test_mistake.py` → `OK`.
<!-- precondition -->Registration starts once the focused tests pass. <!-- postcondition -->It ends
when CLAUDE.md names the skill, both manifests carry the bumped version, CHANGELOG.md has the
entry, and `python tools/spec_check.py work/briefs/mistake-proof.md` prints `SPEC OK`,
<!-- evidence -->shown by the diff of CLAUDE.md, both plugin.json files and CHANGELOG.md, and that
spec_check output. <!-- precondition -->The commit starts once registration is done.
<!-- postcondition -->It ends when the full suite passes, <!-- evidence -->shown by
`python -m unittest discover tests` → `OK`, recorded in BUILD.md.

## Output
<!-- deliverable -->`plugin/skills/mistake-proof/` (SKILL.md, `scripts/mistake.py`,
`scripts/_encoding.py`), `tests/test_mistake.py`, and the registration edits above.
<!-- acceptance -->`tests/test_mistake.py`, each test planting what a stage exists to catch, in a
scratch git repo:
- a revert and a later commit that redoes the reverted change are both mined as candidates;
- `--gate` refuses a class with one piece of evidence, an evidence sha or `file:line` that does
  not exist, and a level-3 class with no `why not` line for levels 1 and 2;
- a check that passes on the past mistake commit is refused as unable to fail; one that fails
  there and passes on the working tree clears the class;
- a check that fails on the current tree because old uses exist is refused with the
  added-lines hint;
- with CI config present, a check command missing from it is refused;
- a rule-table row whose enforcer does not exist is refused, and a level-5 class with evidence
  newer than its row is reported as a repeat;
- an exception with no `approved=`, or with `expires=` in the past, is refused;
- a reply that calls a level-5 class enforced, or names a class the gate did not clear, is
  refused by `--answer-check`; a drafted reply with its slots filled passes;
- the repo's files are byte-identical after a full run, apart from `.mistakes/`;
- one refusal with several gaps names them all.
`tests/test_spec.py` holds this brief once the skill folder exists.
<!-- verification -->`python -m unittest discover tests`
