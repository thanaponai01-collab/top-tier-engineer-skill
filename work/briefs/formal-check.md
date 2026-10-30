# Formal check: prove a property for every case, and keep the proof true to the code

## Intent
<!-- purpose -->Every sibling proves things by example: a test, a repro, a mutation, a check red on
one past commit. Races, retries, state machines and parsers break on the case nobody wrote, so a
green suite says little there. Give an agent a helper that holds a formal check to the same
mechanics as the rest of the plugin: the property is stated in one plain sentence, the check is
seen failing on a broken copy of the code it guards, a failure on the current code stays a
finding instead of a weaker property, and the check is flagged stale the moment the code it
describes changes. Adapted from pstack's prose `create-formal-verification-skill` and
`maintain-formal-verification-skill` (cursor/plugins, `pstack/skills/`); their quality list and
upkeep outcomes become stages and records the helper checks, not steps the agent promises to do.
<!-- end state -->`python plugin/skills/formal-check/scripts/formal.py <repo> --scan` lists candidate
targets (concurrency, retries, state fields, parsers, unsafe code) with `file:line`; `--gate`
refuses until a check has a target, a recorded property, a model mapped to code that exists, a
run that passes on the code (or a finding told as steps), and a break in a covered file that
makes it fail; `--drift` names every check whose covered code changed since its sync commit and
holds it stale until each commit is classified and the check reruns red-then-green at HEAD. The
checks live in the target repo under `.formal/`, so the next agent reruns them with one command.
<!-- done when -->Every condition under Acceptance passes, the skill is registered like its
siblings, and the full suite passes.

## Context
<!-- grounding -->
- The plugin's rule: mechanics, not advice. The helper never judges a model's mathematics; it
  judges what can be run and compared: does the check pass, does it fail with the guarded code
  broken, do the cited lines exist, did the property text change, did the covered code change.
- No sibling covers this. A search of `plugin/skills` for TLA, model checking, property-based and
  formal finds nothing. verify-loop proves one change by example, mistake-proof proves one past
  mistake is caught, debug-protocol proves one cause.
- The dangerous case is a check that keeps passing on a model of code that no longer exists: it
  looks like a proof. Drift is detected from git, not from the agent's memory.
- The verifier (TLA+/TLC, Apalache, Kani, CBMC, Dafny, Hypothesis, a hand-written exhaustive
  enumerator, …) is the target repo's dependency, never ours. To the helper a check is a command
  that exits 0 when the property holds and non-zero when it does not.
- The tests cannot assume Java or TLC. They use a stdlib Python exhaustive enumerator over a toy
  two-thread counter as the verifier, which is a real formal check in the sense that matters
  here: it visits every interleaving within its bound.
- Unlike `.blast/` or `.mistakes/`, `.formal/` is meant to be committed: it is the record the
  next agent reruns.
<!-- scope -->A new manual-only skill `plugin/skills/formal-check/` (SKILL.md, `scripts/formal.py`,
`scripts/_encoding.py`, stdlib only), state and records in `.formal/`; git history and tracked
text files of the target repo; `tests/test_formal.py`; registration in CLAUDE.md, both plugin
manifests' version and CHANGELOG.md; `.formal/` added to the other helpers' skip lists.
<!-- non-goals -->
- Writing the model, harness or properties: the agent writes them; the helper only judges whether
  they can fail, point at real code, and still describe it.
- Installing a verifier, downloading anything, or calling the network. A missing tool makes the
  check `blocked`, with the command that failed.
- Parsing TLA+, Rust, Dafny or any model language. Mapping is by cited `file:line` and by literal
  model-element text found in the model file.
- Drawing statecharts or diagrams (pstack's `statechart`). A counterexample is told as steps in
  the code's words.
- Fixing product code when a property fails: that is a finding for debug-protocol or the user.
- Blocking verify-loop or safe-release on a stale check: this slice only reports.

## Guardrails
<!-- constraints -->
- One helper `F` = `python <skill>/scripts/formal.py <repo>`: `F --scan` lists candidate
  targets; `F --gate [NAME]` checks every stage of every check (or one) and drafts
  `.formal/answer.md`; `F --drift [NAME]` lists commits since each sync commit that touched a
  covered file, renames followed; `F --answer-check FILE` refuses a reply that claims more than
  the gate saw.
- Each check is one file `.formal/<name>.md` with one-line fields: `- property:` and `- harm:`
  (one plain sentence each), `- target: <file:line>` (the promise in the code), `- tool: <name>
  <version>`, `` - cmd: `<command>` ``, `- model: <path>` (one or more), `- map: <model element>
  -> <file:line>` (one or more), `- covers: <path>` (one or more), `- bounds:` and
  `- assumes:` (what the pass does not cover), and a break (`- break: <file>`, `` - old: `<text>`
  ``, `` - new: `<text>` ``, the same shape as blast-radius).
- A map line is refused when its `file:line` does not exist, its model element text is not in the
  model file, or the file is not in `covers`. Every `covers` path needs at least one map line.
- The break must edit a `covers` file, never a model file, and `old` must occur once. The helper
  runs `cmd` on a scratch copy of the working tree (must pass) and on one with the break applied
  (must fail). A check that passes with the break applied is refused as one that cannot fail.
- When `cmd` fails on the unbroken code, the check is a finding, not a refusal: it needs
  `- step: <what happens> <file:line>` lines, two or more, each citing a line that exists, and
  the answer reports it as a bug in the code.
- On its first green run the helper records the property, bounds and assumes text with a hash
  in `.formal/<name>.lock`. Any later change to those three fields is refused unless the check
  file carries `- changed: <old> -> <new> evidence: <sha|file:line>` naming a commit or line that
  exists. A reduced bound is always reported in the answer.
- `cmd` must finish within a time limit (600 s by default, `--budget SECONDS` to change it); the
  measured time is printed. Over the limit the check is refused as too slow to rerun.
- The sync commit lives in the lock file and only the helper writes it: after a green run with
  the break red, at the current HEAD with a clean tree for the covered files. A check whose
  covered files changed since then is `stale`; `--drift` drafts one line per commit in
  `.formal/<name>.drift.md`: `- <sha>: no-effect|reshaped|promise-changed|suspect: <why>`, and
  `promise-changed` cites evidence. The gate holds a stale check until every commit has a line
  and the rerun passes, then it becomes `updated` (or `bug` if the rerun fails with steps).
- Each check ends in one outcome, which the gate sets and the answer must use: `in-sync`,
  `updated`, `bug`, or `blocked` (tool missing, command errors, budget exceeded).
- If the repo has CI config (`.github/workflows/`, `.gitlab-ci.yml` and the like), each `cmd`
  must appear in it; with no CI the answer says so.
- SKILL.md body ≤ 5,000 chars, shaped like blast-radius's (goal, `F`, stages table).
<!-- invariants -->
- The helper never writes the product tree: runs and breaks happen in scratch copies; only
  `.formal/` changes.
- A property, bound or assumption never changes silently: every change has a `changed` line with
  evidence, and the lock records it.
- Every refusal lists all problems at once, each with the line or command that fixes it.
- `.formal/` is skipped by the other helpers' scans, and `.verify-state`, `.wire`, `.features`,
  `.release`, `.evolve`, `.perf`, `.blast`, `.mistakes` are skipped by this one.
<!-- escalation -->Whether the helper should also render a project-local skill (pstack's approach)
or rely on `.formal/` plus CI is left for the user after this slice. Whether a stale check should
block verify-loop or safe-release is a cross-skill decision for the user; this slice only
reports.

## Freedom
<!-- latitude -->How `--scan` finds and ranks candidates, how scratch copies are made (worktree,
copy, or archive), how renames are followed, how the time limit is enforced, the wording of
drafts and refusals, and the order of work. The agent chooses the target, the tool and the
model. Only the command contract, the check, lock and drift file formats, the break-must-fail
rule, the property lock, the outcomes and the Acceptance tests are fixed.

## Gates
<!-- precondition -->Rejection starts once `tests/test_formal.py` is written.
<!-- postcondition -->It ends when it fails because `formal.py` does not exist or does not catch
each plant, <!-- evidence -->shown by the retained failing output, named in BUILD.md.
<!-- precondition -->Implementation starts once the tests fail for the right reason.
<!-- postcondition -->It ends when the focused tests pass, <!-- evidence -->shown by
`python -m unittest discover -s tests -p test_formal.py` → `OK`.
<!-- precondition -->Registration starts once the focused tests pass. <!-- postcondition -->It ends
when CLAUDE.md names the skill, both manifests carry the bumped version, CHANGELOG.md has the
entry, and `python tools/spec_check.py work/briefs/formal-check.md` prints `SPEC OK`,
<!-- evidence -->shown by the diff of CLAUDE.md, both plugin.json files and CHANGELOG.md, and that
spec_check output. <!-- precondition -->The commit starts once registration is done.
<!-- postcondition -->It ends when the full suite passes, <!-- evidence -->shown by
`python -m unittest discover tests` → `OK`, recorded in BUILD.md.

## Output
<!-- deliverable -->`plugin/skills/formal-check/` (SKILL.md, `scripts/formal.py`,
`scripts/_encoding.py`), `tests/test_formal.py`, and the registration edits above.
<!-- acceptance -->`tests/test_formal.py`, each test planting what a stage exists to catch, in a
scratch git repo holding a two-thread counter and a stdlib enumerator over its interleavings:
- `--scan` lists the counter's lock and retry lines as candidates with `file:line`;
- `--gate` refuses a map line whose `file:line` does not exist, whose element is not in the model
  file, or whose file is not covered, and a `covers` path with no map line;
- a break that edits the model file, or whose `old` text is missing, is refused; a check that
  still passes with the break applied is refused as unable to fail; one that passes clean and
  fails broken clears;
- with the lock removed from the counter, `cmd` fails clean: without `step` lines the gate
  refuses, with two cited steps the outcome is `bug`;
- changing the property or lowering the bound after the first green run is refused without a
  `changed` line, and accepted with one whose evidence exists;
- a command over `--budget` is refused as too slow, and a missing tool gives `blocked`;
- a commit that edits a covered file makes the check `stale`; it stays held until the drift file
  has a line for that commit and the rerun passes, then it is `updated` and the sync commit is
  the new HEAD; a renamed covered file is still followed;
- with CI config present, a `cmd` missing from it is refused;
- a reply that calls a stale or `bug` check verified, or names an outcome the gate did not set, is
  refused by `--answer-check`; the drafted reply with its slots filled passes;
- the repo's files are byte-identical after a full run, apart from `.formal/`;
- one refusal with several gaps names them all.
`tests/test_spec.py` holds this brief once the skill folder exists.
<!-- verification -->`python -m unittest discover tests`
