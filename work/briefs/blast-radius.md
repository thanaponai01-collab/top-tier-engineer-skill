# Blast radius: what a change breaks outside its diff

## Intent
<!-- purpose -->A change can be proven to do what it meant (verify-loop) and be wired in (wire-check)
and still break code it never touched: a caller that passes the old arguments, a reader of a
JSON key or column it renamed, a script that reads an env var it dropped. Nothing in the plugin
looks there. Give an agent a helper that lists every consumer outside the diff and will not let
it call the change safe until the one fact the change is safe because of has been run, and was
seen failing with that fact broken. Adapted from pstack's prose `blast-radius` skill
(cursor/plugins, `pstack/skills/blast-radius/SKILL.md`); its 1-to-5 sureness ladder becomes a
level the helper records, not a level the agent claims.
<!-- end state -->`python plugin/skills/blast-radius/scripts/blast.py <repo> --base <ref>` names every
consumer of what the diff changed; `--gate` refuses until each has a verdict and the safety fact
has a proof that fails on the broken fact and passes on the change; the drafted answer prints the
ladder level the helper saw, and says `unproven` when it saw less than a run.
<!-- done when -->Every condition under Acceptance passes, the skill is registered like its siblings,
and the full suite passes.

## Context
<!-- grounding -->
- The plugin's rule: mechanics, not advice. A blast-radius writeup that sounds right reads the
  same whether or not it is true, so only what the helper ran or checked counts.
- verify-loop's `review` judges only changed lines (UNCOVERED, SURVIVED, UNMAPPED, LOOSENED);
  wire-check asks whether anything reaches new code. Neither asks who depended on the old
  behaviour, so this is a gap, not an overlap.
- Breakage a symbol search misses is the point: string uses of a changed name (dict keys, JSON
  fields, column names, env vars, flag names, CLI options) in any text file, and callers several
  imports away.
- Most risky-looking changes are safe because of one fact ("this call only drops cache entries
  that are already dead"). Proving that one fact clears most risks at once; a long list of maybes
  does not.
- Sureness ladder: 1 said so, 2 cited `file:line`, 3 walked the failure, 4 ran it (a command that
  fails when the fact is false), 5 reproduced in the running app.
<!-- scope -->A new manual-only skill `plugin/skills/blast-radius/` (SKILL.md and `scripts/blast.py`,
stdlib only), state in `.blast/`; Python symbols by AST, every other tracked text file by literal
name; `tests/test_blast.py`; registration in CLAUDE.md, both plugin manifests' version and
CHANGELOG.md.
<!-- non-goals -->
- Fixing what it finds: report only, like latent-audit and wire-check.
- Running several models on the same question (pstack's `arena` step).
- Symbol resolution for languages other than Python; they get literal-name matching only.
- Consumers outside the repo (other services, other repos): they get an `unknown` verdict naming
  what they depend on, not a search.
- Changing verify-loop's `review`; a pointer from its output can come later.

## Guardrails
<!-- constraints -->
- One helper `B` = `python <skill>/scripts/blast.py <repo>`: `B --base REF` lists, `B --gate`
  checks the stages and drafts the answer, `B --answer-check FILE` refuses a bad answer.
- Every consumer outside the diff gets a line in `.blast/verdicts.md`:
  `- <file:line>: breaks|cleared|unknown: <why>`; `breaks` and `cleared` cite the `file:line` or
  library source they rest on; `unknown` says what it depends on. The gate drafts the slots.
- The safety fact lives in `.blast/fact.md` with its proof command and a break: one explicit edit
  that makes the fact false. The helper runs the proof on a scratch copy of the change (must pass)
  and on a copy with the break applied (must fail). A proof that passes both is refused as one
  that cannot fail.
- The answer's level is the highest the helper saw, never a number the agent typed: 4 needs the
  proof seen red then green; 5 needs a `--app "<cmd>"` run that shows the same. Below 4 the
  answer says `unproven`, and a `safe` verdict is refused.
- SKILL.md body ≤ 5,000 chars, shaped like wire-check's (goal, `B`, stages table).
<!-- invariants -->
- The product tree is never written: proofs and breaks run in scratch copies; only `.blast/`
  changes.
- Every refusal lists all problems at once, each with the line or command that fixes it.
- `.blast/` is skipped by the other helpers, and `.verify-state`, `.wire`, `.features`,
  `.release`, `.evolve`, `.perf` are skipped by this one (as in 320d3696).
<!-- escalation -->Whether a `breaks` finding should block `safe-release`'s gate is a cross-skill decision
for the user; this slice only reports.

## Freedom
<!-- latitude -->How consumers are found and ranked, how the break is expressed (a patch, an
old/new string pair, or reuse of verify-loop's one-mutation code), the wording of verdict lines
and the drafted answer, and the order of work. Only the command contract, the verdict format,
the level rule and the Acceptance tests are fixed.

## Gates
<!-- precondition -->Rejection before implementation starts once `tests/test_blast.py` is
written. <!-- postcondition -->It ends when it fails because `blast.py` does not exist or does not
catch each plant, <!-- evidence -->shown by the retained failing output, named in BUILD.md.
<!-- precondition -->Implementation starts once the tests fail for the right reason.
<!-- postcondition -->It ends when the focused tests pass, <!-- evidence -->shown by
`python -m unittest discover -s tests -p test_blast.py` → `OK`. <!-- precondition -->Registration
starts once the focused tests pass. <!-- postcondition -->It ends when CLAUDE.md names the skill,
both manifests carry the bumped version, CHANGELOG.md has the entry, and
`python tools/spec_check.py work/briefs/blast-radius.md` prints `SPEC OK`, <!-- evidence -->shown by
the diff of CLAUDE.md, both plugin.json files and CHANGELOG.md, and that spec_check output.
<!-- precondition -->The commit starts once registration is done. <!-- postcondition -->It ends when
the full suite passes, <!-- evidence -->shown by `python -m unittest discover tests` → `OK`,
recorded in BUILD.md.

## Output
<!-- deliverable -->`plugin/skills/blast-radius/` (SKILL.md, `scripts/blast.py`, `scripts/_encoding.py`),
`tests/test_blast.py`, and the registration edits above.
<!-- acceptance -->`tests/test_blast.py`, each test planting what a stage exists to catch:
- a function whose signature changed is listed with its caller in another module;
- a dict key renamed in a producer is listed with a consumer that reads the old key as a string
  in a file the diff did not touch, including a non-Python file;
- `--gate` refuses while any listed consumer has no verdict, and a `breaks`/`cleared` verdict
  with no `file:line`;
- a proof that passes with the break applied is refused as unable to fail; one that fails with
  the break and passes on the change brings the level to 4;
- an answer that says `safe` below level 4, or states a level above the one recorded, is refused
  by `--answer-check`; a drafted answer with its slots filled passes;
- the repo's files are byte-identical after a full run, apart from `.blast/`;
- one refusal with several gaps names them all.
`tests/test_spec.py` holds this brief once the skill folder exists.
<!-- verification -->`python -m unittest discover tests`
