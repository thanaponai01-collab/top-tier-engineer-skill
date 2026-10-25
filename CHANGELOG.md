# Changelog

## 1.26.0 - 2026-10-25 - feature-map proves what it maps, and tells the next agent

- **Receipts behind `proven`.** `features.py prove --feature X -- <command>` runs an entry point and
  keeps `.features/<feature>.json`: the command, exit code, output tail (local paths become
  `<repo>`), and a hash of every file the feature names. `--copy` runs it in a throwaway copy, so
  an entry point that writes never touches real data; `--file` + `--note` records a screenshot by
  hash. `proven` needs a passing receipt for every entry point (new `unproven` count, replacing
  `unpinned`); drift is a changed file hash, so it works without git and cannot be re-pinned
  without a run. New label `failing` needs a failed run on record. `prove --again` re-runs and
  re-records every receipt; a receipt for an entry point the map no longer has is pruned.
- **`check --rerun`** re-runs every recorded command and fails (`regressed`) when one that passed
  fails now: the drift alarm for behaviour, not just declarations.
- **The map carries its own alarm.** `init`/`prove` vendor a single-file copy of the checker into
  `.features/features.py`, so a later session or CI runs `check --rerun` with no skill installed.
  New `unannounced` count (red under `--strict`): no `AGENTS.md`/`CLAUDE.md` line points at
  `FEATURES.md` and its check; `check` prints the line to add. `init`'s header lists the commands.
- **`## Not features`**: an entry point the scan finds that is not a feature (debug command,
  test-only selector) is listed with its reason; without a reason it stays unmapped, and it goes
  STALE like any line when the code drops it. `## Not built` is no longer counted as a feature.
- **Trace start is checked**: a first trace step neither in nor called from an entry point's file is
  BROKEN.
- **CLI anchors** must appear as a quoted command name or a `def name(`: a renamed subcommand whose
  module keeps the old name (`search.run`) is now STALE.
- **verify-loop is optional**: a feature needs a VERIFY.md link only once the repo has a VERIFY.md.
  The eval showed the old rule dragged every map into writing checks and running `advance` /
  `challenge` (17-20 turns, $0.58-0.70 a try); after it, 6-10 turns and $0.24-0.31.
- `check` prints the exact `prove` line for each unproven entry point and a closing `Proof:` line
  (what ran here, in a copy, failing, never run), so agents stop reading the script to learn it.
- Evals: `feature-map-dead-command-and-destructive` brought from main; new
  `feature-map-crash-only-when-run`, `feature-map-map-survives-change` and
  `feature-map-large-map-survives-change` (two sessions; the runner gains per-session `before`
  scripts and `bare` sessions). All grade the person's data on outcome (`purge` leaves
  `purge.log`), not on a `purge --yes` regex that failed safe runs in a copy.
- **Measured: when asked to check everything, no gain over plain Opus 5.5.** 3 tries per arm:
  dead-command 3/3 vs 3/3 ($0.28 vs $0.13); crash-only 2/3 vs 3/3 ($0.28 vs $0.15; one judge miss,
  one grader timeout that passes on re-grade); map-survives-change 3/3 vs 3/3 ($0.50 vs $0.31);
  30-command handoff 3/3 vs 3/3 ($0.83 vs $0.45; second session $0.31-0.37 vs $0.21-0.28).
  Plain Opus writes its own AGENTS.md/CLAUDE.md and re-runs every command in a sandbox, so it
  finds runtime breaks unaided; the skill's receipts are upkeep it does not need at these sizes.
  133-command handoff (`feature-map-huge-map-survives-change`, 4 planted changes): 3/3 vs 3/3
  ($0.93-1.21 vs $0.60-0.65; second session $0.38-0.53 vs $0.30-0.39). Plain Opus scripts a sweep
  over every command. The with arm's 3 first-pass fails were a grader bug (it wanted one file;
  the skill splits big maps into `include:` area files); fixed to read all notes files, re-graded.
- **Where it helps: a narrow follow-up task.** `feature-map-alarm-on-narrow-task`: same 133-command
  handoff, but session 2 is only asked to document the `show-mood` rename. With the skill's map,
  session 2 ran `check --rerun` (as the announced AGENTS.md line says) and raised the three
  unmentioned breaks: 8 of 9 found, 2/3 tries pass (the miss named the inverted rating check via
  `by-rating`, which shares the parser). Plain Opus did the rename only: 0 of 9 found, 0/3. Cost
  $0.87-0.93 vs $0.39 a try; session 2 alone $0.27-0.32 vs $0.10-0.12.
- The `unannounced` line now spells out the upkeep loop (`check --rerun`, fix lines,
  `prove --again`), after the eval showed later sessions reading the script to learn it.

## 1.25.0 - 2026-10-25 - feature-map reads verify-loop's receipts

- `features.py check` now links each feature to verify-loop, not just to a VERIFY.md heading:
  - **unbacked**: a `proven` feature whose linked section has no receipt of its check rejecting a
    wrong product, or whose check failed in the last run. Read from `verify.py status --json` when
    verify-loop is installed beside feature-map (it is in this plugin); a standalone copy says
    receipts were not checked and judges nothing.
  - **unfenced**: the linked section has no `path:`, or the feature's entry or trace files lie
    outside it, so `verify.py run --affected` would not rerun its check when they change.
  - Both are red under `--strict`. Five tests in `tests/test_features.py` build real verify-loop
    receipts, including a standalone copy with no verify-loop beside it.
- SKILL.md step 5 asks for a covering `path:` and a receipt from `verify.py advance`.

## 1.24.1 - 2026-10-25 - feature-map's check goes red on drift it used to call ok

- `features.py check` matched needles as substrings, so five kinds of drift passed. Each now fails,
  with a test in `tests/test_features.py` (the first feature-map tests here):
  - a renamed selector (`pay-btn` to `pay-btn-v2`) is STALE: needles match as whole tokens;
  - a changed shortcut (`Ctrl+Enter` to `ctrl+shift+enter`) is STALE: the whole combo must appear
    in a quoted string, not just its last key;
  - a trace call left only in a comment is BROKEN: comments are stripped before counting calls;
  - a `verify:` link with no VERIFY.md in the repo counts as unlinked;
  - `proven` with no `@ <sha>` is a new `unpinned` count, red under `--strict`.
- A route no longer passes because its path is a substring of the file name (`/s` in `src/`).
- SKILL.md and the script docstring describe the new matching and counts; SKILL.md no longer names
  `wire-check`, `arch-map` or `recall`, which this plugin does not ship.

## 1.24.0 - 2026-10-25 - feature-map ships in the plugin

- New skill `plugin/skills/feature-map/`, copied unchanged from top-tier-engineer main (4.66.0):
  `FEATURES.md` lists each feature, its entry points (route, click, shortcut, cli, menu), a
  `trace:` call chain and the VERIFY.md section that proves it. `scripts/features.py init` drafts
  it from the code, `check --strict` fails on stale or broken entries, `impact` lists the features
  and VERIFY.md sections a change touches.
- Manual-only (`disable-model-invocation: true`), so it adds nothing to verify-loop's trigger
  surface. It names `wire-check`, `arch-map` and `recall`, which this plugin does not ship; the
  skill says it stands without them.
- Not yet covered here: its eval case `feature-map-dead-command-and-destructive` stays on main, and
  `tests/` has no feature-map tests.

## 1.23.0 - 2026-10-25 - A trigger eval, and a description that fires on people's words

- New `evals/trigger.py`: 26 prompts (13 should load verify-loop, 13 should not), each run headless
  in a small billing repo with an uncommitted change, with only this plugin loaded. Every try is
  checked for isolation from its init event: a user skill, another plugin, an MCP server or a
  non-empty `~/.claude/CLAUDE.md` makes the try invalid. Prompts are split train/test so a
  description tuned on train is judged on prompts it was not fitted to. `--description FILE`
  scores a candidate on a staged copy without touching the plugin.
- The old description fired only on the words "verify", "prove" or "proof": Opus 5.5 9/26 wanted
  tries, Sonnet 5.5 4/13. "Make sure it works before I commit", "another agent said it's done",
  "would our tests notice" and "green means it works" never loaded it.
- New description, in the intents people use. Opus 5.5: train 6/14 -> 14/14, held-out test 3/12
  -> 10/12. Sonnet 5.5: train 3/7 -> 7/7, test 1/6 -> 4/6. False fires 0 before and after on both.
  Still missed on both models (held out, not tuned for): "double-check the fix before I merge".
- `evals/trigger/measured.json` holds the description last scored; `tests/test_trigger.py` fails
  when SKILL.md's description differs from it, so a description edit has to be re-measured.

## 1.22.0 - 2026-10-25 - Survey scores in report, require: fresh, an overfit eval

- `report` prints `SURVEY <feature>: N/M generated mutants caught` for the last `challenge --auto`
  on the current checks and tree. Before, a 10/10 survey still read "nothing here is proven able
  to fail". It stays a lead, not a receipt: `GAP never seen red` and the `prove` step remain until
  a spec-backed rejection is recorded. `report --json` gains `surveys`. The score lives in the cache
  (`surveys.json`), so a survey still writes no receipt and leaves .verify-state.json untouched.
- `require: fresh` keeps `run --strict` red (`NO FRESH INPUTS`) for any non-journey feature with
  checks and no `fresh: N`. `report` lists it as `GAP no fresh inputs` with a `map` step, ordered
  before `prove` because adding `fresh:` changes the check signature. `run --json` gains `no_fresh`.
- New eval case `verify-loop-special-cased-product`: the fix rounds only when the percentage is a
  multiple of 5, and every test case is one. The checks are green, proven red, and 10/10 mutants
  are caught. First run (3 tries per arm, Opus 5.5): 3/3 without the skill, 3/3 with it, at $0.10
  vs $0.17 a try. No try in either arm used `fresh:`. Bare Opus found the guard by reading the
  code, so this case does not show the skill helping.

## 1.21.0 - 2026-10-25 - Fresh inputs: product code that special-cases its tests

Anthropic's formal-verification work (anthropic.com/research/formal-verification) names the main
failure of a prove-and-patch loop: the model changes the program so the check passes trivially.
verify-loop guarded the check (`HOLLOW`, `LOOSENED`, `CHECK CHANGED`) but not the product side.
Product code such as `if (credit, amount) == (100, 50): return 150` passes its fixed case, and
every mutation on that line is caught, so the mutation score looks perfect.

- A feature bullet `fresh: N` (1-20) makes `run` repeat the feature's passing checks N times,
  each with a random `VERIFY_SEED` the check draws its cases from. A red fresh run is `OVERFIT`:
  the run is red, the seed is printed with a reproduce command, and `report` makes it a `fix` step
  that says to fix the product, not the check.
- The own cases always run with `VERIFY_SEED` unset, even when the caller's environment sets it.
- `SEED UNUSED` (red, and a `repair` step while unfrozen): `fresh:` is declared but no test file,
  script, oracle or command of the feature names `VERIFY_SEED`.
- An invalid `fresh:` value is `BROKEN`. Before 1.21.0 the bullet was parsed as a shell command.
- `fresh:` is frozen by `baseline`: removing it is `CHECK CHANGED`; a re-baseline that lowers N
  is listed for review, and raising it is not. Recipes without `fresh:` keep their signatures.
- `run --json` summary gains `overfit` and `seed_unused`.

The guard is opt-in and only as good as the check's generator: it cannot tell overfitting from a
generator that disagrees with its oracle, and it is not run inside `challenge` copies.

## 1.20.0 - 2026-10-24 - Claude Code's own /verify

Claude Code now ships a built-in `/verify` and, since v2.1.286, runs a project skill named
`verify` that Claude can invoke before each commit that is not docs or tests only. Create mode
generates exactly that skill.

- The generated skill has a `## Before a commit` section that runs only
  `verify.py run . --affected`, so the per-commit run no longer launches and drives the whole app.
  `skill-check` reports the section missing, or present without that command, and so does
  `maintain`: a skill generated before 1.20.0 is flagged until the section is added.
- `scaffold-skill --adopt` keeps a SKILL.md already at `.claude/skills/verify/` (where the built-in
  `/verify` records its recipe) and adds only what is missing: frontmatter, the VERIFY.md link,
  required sections and feature files. It never overwrites a feature file, and a second run
  changes nothing. Without `--adopt`, the refusal now names it.
- `examples/verify-create/` and the create reference carry the new section; the reference names
  the monorepo call form `/<package path>:verify`.

Also released in 1.20.0, from the automatic progression work:

- Add `verify.py advance`: bounded check runs and proof-ready baseline freezing, with structured
  agent tasks and the canonical verdict. Preserve existing proof and independence gates.
- Stop for foreign claims, executor contention, stale inputs, blocked environments and unchanged
  strict failures; retain the last executed transition batch in existing agent state.
- Add CLI regression coverage for progression, stop conditions, limits and external state.
- `run` records `HOLLOW` features in state, and `report` gives a hollow check that is not frozen a
  `repair` step: fixing it is the work, not a finding for a person. In the 1.18.2 eval, all three
  skill runs of `make-it-verified` stopped to ask before repointing the hollow test.
- In `challenge --auto`, report that an uncovered or surviving mutation "still passed" (e.g.
  `breaking <before> (-> <after>) still passed`), making check passivity explicit in tool output.
- Promote `advance` as the primary progression driver in `SKILL.md`: `advance` automatically freezes
  proof-ready baselines and runs strict check passes, yielding only judgment tasks to the agent.
- Clean up unmanaged file handles and explicit UTF-8 encodings across scripts, evals, and tests,
  eliminating ResourceWarning unclosed file leaks on Windows and non-POSIX platforms.
- Broaden phrase matcher inflection coverage in `ci-fresh-proof` eval to accept natural variants of
  unbacked state rejection (e.g. "ignores", "excluded", "didn't trust", "left out").

### The lazy path is the correct path

Eval runs showed where turns went: agents grepped `gates.py` to learn why `answer-check` said
`MISSING`, chained 4–5 helper calls to answer one read-only question, and pasted `NEXT` commands
that named a bare `verify.py`. Each of these is now a helper mechanic.

- Add `verify.py assess`: one read-only call runs every check, surveys each passing feature with
  `challenge --auto` (its `path:` files, or with no `path:` the files its checks imported), and
  prints `report` and an answer draft. It replaces the three-command Assess section.
- Survivors of that survey become `GAP survived a wrong result` in `report`, and `answer-check`
  asks the answer to name them, so a copied draft cannot drop the finding.
- `report`, `assess` and `advance` end with an `ANSWER DRAFT` the helper writes from what it knows,
  with `[[fill: ...]]` slots only for judgment, and a `Then:` line with the runnable
  `answer-check` command on the same state.
- `answer-check` lists every problem in one pass with its fix (`--json`: `fix`), ends with
  `ADD THESE LINES`, and rejects an unfilled slot as `ANSWER UNFILLED`.
- `NEXT` commands name the helper's real path, quoted, so they run when pasted.
- `advance` keeps two lines of a passing step's output and the tail of a failing one; plain output
  shows the failing tail and the draft, so `--json` is no longer needed to see why a step failed.
- SKILL.md is a router: one command per question, "read the output, not the scripts", the task
  table, the done rule and the answer path. Body 6.9 KB → 4.9 KB. `tests/test_agent_path.py` holds
  it to 5,000 characters, and checks that every command, link, anchor and verdict name it uses exists.

## 1.18.2 - 2026-10-21 - A missing `python` says so

- A check that fails because `python` is not on PATH while `python3` is (sh, bash, dash, zsh,
  Windows, or the macOS `xcode-select` stub) is now `BLOCKED` with that cause and how to provide
  `python` (a virtualenv or a wrapper; not a symlink to macOS's `/usr/bin/python3` stub). Changing the
  check to `python3` is named as a check edit. Recipes and examples keep `python`.
- The macOS stub's `Failed to locate '<tool>'` and dash's `sh: 1: <tool>: not found` count as
  environment failures; before, the stub's red read as a product failure.
- The Codex `plugin.json` is back in step with the Claude one.

## 1.18.1 - 2026-10-21 - Gates, reviewed

Fixes from a review of 1.18.0:

- `LOOSENED` no longer counts an assertion's message as an expected value, so rewording a message
  is not a loosening. A loosening a person reviewed before it was committed stays reviewed after the
  commit (findings are keyed by file, test and what changed, not by commit).
- `WEAK SIGNAL` strips only runner exit codes, test counts and line numbers. `expected status 200`
  names a behavior again.
- `answer-check` matches gap items as whole words or paths: a feature named `Total` is not
  "named" by the word "totality".
- `UNMAPPED`: `python tools/app.py` in a command no longer maps a root `app.py`.
- Receipts share one stored tree per run (`receipt_trees` in the state, `files_id` on each
  receipt) instead of each carrying a full-tree hash map. `report` and `status` hash the tree for
  receipt checks once instead of three times.

## 1.18.0 - 2026-10-21 - Gates: the model creates, the helper judges

Six rules that SKILL.md only asked for are now verdicts `verify.py` prints and `run --strict`
enforces (new `scripts/gates.py`, tests in `tests/test_gates.py`). The agent still chooses the claim,
writes the check and picks the wrong state; the helper no longer takes its word for any of them.

- **`answer-check`.** `verify.py answer-check <repo> --answer <file>` holds the agent's final answer
  to `report`: it must say `VERDICT: <verdict>`, must not say "ready to merge", "all checks pass",
  "fully verified" and the like unless the verdict is green, and must name every gap item. "Every
  `GAP` goes in the answer" was prose; now an answer that drops one exits 1.
- **`UNMAPPED`.** Product source that no feature's `path:`, command, `oracle:`, coverage map or a
  mapped test's imports reach is a `GAP unmapped` and keeps strict red, unless a blind spot names it.
  Fixes the `green-with-unverified` blind spot (`search.py`), which both eval arms missed 0/3.
- **`WEAK SIGNAL`.** A `fail-signal:` that is only runner boilerplate (`FAILED`, `AssertionError`,
  `exit code 1`) proves nothing: any failure prints it. The make-it-verified reference solution's
  `AssertionError:` signal is now `refund credit mismatch`, with a message in its assertion.
- **`PROOF NOT FROM PRODUCT`.** Failure receipts now record every file's hash. Once the check is
  green again, a receipt counts only if a product file (inside `path:` when given) differed when it
  went red; a red on the same files came from the environment. Turns "put the bug in, restore" into
  a check. Receipts from before 1.18.0 must be proved again.
- **`LOOSENED`.** For each mapped test file, the last 30 commits and the working tree are compared
  test by test: removed, skipped, fewer assertions, an exact assertion made tolerant
  (`assertEqual` -> `assertAlmostEqual(delta=2)`), or the same assertions with new expected values.
  Each is listed with commit, author and subject; strict stays red and `baseline` refuses until a
  person reviews it (`--reviewed-by --reason`). Catches `teammate-loosened-check`, where no baseline
  existed for `CHECK CHANGED` to compare against.
- **`BLOCKED`.** A failing check whose output is a missing tool, dependency, port or timeout is
  printed as `BLOCKED`, listed as `GAP blocked by the environment`, and its `NEXT` step is
  `[blocked]` (never claimable in a swarm) instead of `[fix]`.
- `ci` resolves its scratch folder, so the CI tests pass on macOS (`/var` vs `/private/var`).

Not solved, and said so: `VERIFY_AGENT` and `--reviewed-by` are names the agent supplies. Only CI
that the agent cannot reach makes independence or review more than self-declared.

## 1.17.0 - 2026-10-21 - Mechanism, not advice

SKILL.md is cut from 148 lines to 99 and rebuilt around the helper as a state machine: run
`report`, then do the step its `NEXT` line names (`map`, `fix`, `prove`, `freeze`, `challenge`,
`independent`, `run`). A rule stays only if the evals show the skill arm beating the bare arm on
it, or `verify.py` enforces it and the agent must know it to act on a verdict. The per-rule
evidence is in `evals/SKILL_CUTS.md`. No agent runs were paid for; it rests on the historical
ledger and run logs (`ddcd651~1:evals/`), the 2026-10-20 run and this changelog.

- **Cut "A good check" items 2–5.** "Watches the real thing": `fake-check-and-decoy` was 3/3
  both ways, and `HOLLOW` now flags the pattern. "Expects what the spec says": no difference on
  `healthy-check` or the decoy case, and `references/answer.md` already says it. "Fails
  specifically" and "one cheap command": never measured, and both are advice. Item 1 ("can fail")
  stays as the `prove` step, which won `check-cannot-fail` (0/3 → 1/3; the winning run broke the
  code and ran the check) and `make-it-verified` (the bare arm left no `fail-proof:` or baseline).
- **Cut the check-strength ladder and "name the claim observably".** Neither was measured, both
  are advice, and the claim wording is in `references/answer.md`.
- **Cut the artifact-identity bullet.** `p07-running-artifact-identity` showed no difference
  (1/1 vs 1/1, and replays missed the same finding on both sides). It stays in
  `VERIFY_FORMAT.md#run` and `references/project-recipe.md`.
- **Cut the fooled-checker intro, "an assessment edits no product code", `tests --strict` and
  the closing *Test:* line.** All four were unmeasured or duplicated: assess mode is defined in
  `references/answer.md`, `tests --strict` is in `references/verify-change.md`, and the *Test:*
  line repeated Done. The guards themselves (`baseline` before the work, `require: independent`,
  sealed state, CI) stay, one line each, because the helper enforces them.
- **Kept, prominent: "a check you think is wrong is a finding, not an edit."** `check-is-wrong`
  went 0/3 → 3/3, and none of the three winning runs called the helper. The prose did this alone.
- **Kept because the helper enforces them:** the `--assess` quick path (added in 1.16.0 after an
  eval agent skipped the helper because it wrote into the repo), Done, `NEWLY RED` /
  `SAME FAILURE x2` / `BUDGET`, `SWARM:` and the no-second-name rule, `--reviewed-by`, `HOLLOW`
  / `SURVIVED` / `UNCOVERED`.
- **Kept, flagged as needing a mechanism:** green covers mapped features only. In
  `green-with-unverified` (0/3 vs 0/3) both arms missed the unproven checks, which `report` now
  prints as `GAP never seen red`. But `report` still prints `0 unverified` for `search.py`, a
  feature with no section, so SKILL.md tells the agent to add what no feature maps. The fix is a
  `report` gap for unmapped product files.
- **New guards for the structural cases** (not run yet): never skip, mock, stub, loosen or drop a
  check to get green, and a check that cannot run here stays red and is reported as blocked
  (`real-check-unavailable`). A note saying a check went red is a claim and only a receipt
  counts (`inherited-claim`). `references/triage.md` gains the missing-tool case.
- Step-number references in `references/answer.md` and `references/helpers.md` now name the
  `prove` step. No test asserted SKILL.md prose; `python -m unittest discover tests` passes
  unchanged.

## 1.16.0 - 2026-10-20 - Assess without touching the repo

- **`--assess` and `--state-dir DIR` keep every helper write outside the checked repo.** Every subcommand takes them, and `VERIFY_STATE_DIR` does the same from the environment. The state files, the lock and the caches go to `<dir>/<repo name>-<path hash>/`; `--assess` defaults the dir to `verify-loop-assess` in the system temp directory and also stops Python checks from writing bytecode or a pytest cache. After `run --assess`, `challenge --auto --assess` and `report --assess`, `git status --porcelain` of the repo is unchanged, and `report` reads the state back. `NEXT` and `review` reproduce commands carry `--state-dir` so follow-ups land in the same place. Scratch copies made by `challenge`, `swarm --auto` and `ci` keep their state inside themselves, so nothing is left behind for them. Before this, every `run` wrote `.verify-state.json` into the repo, and in the 2026-10-20 eval an agent skipped the helper for that reason. Without the options nothing changes. Files the checks themselves write and the `scaffold-*` commands, which exist to add project files, are not moved.
- **SKILL.md opens with the assess path.** Three commands (`run`, `challenge --auto`, `report`, all `--assess`) answer "is this check or claim any good?" before the full loop, with `path:` lines named as what sharpens `HOLLOW` and lets `challenge --auto` run without a file. The helper command list now points to `references/helpers.md` instead of repeating it.

## 1.15.0 - 2026-10-20 - Hollow passes go red

- **`run` flags a check that never runs the product.** When a feature names Python files with functions in `path:`, `run` measures its checks. If they all pass without calling one of those functions, the feature is `HOLLOW` and the run is red, strict or not. Examples are a test that loads no cases and loops over `[]`, a test that skips, or a test that checks a copy of the logic. Importing the module does not count, since an import runs module code, not the behavior. A feature with no `path:` is judged on the non-test repo code its checks imported. It is `HOLLOW` when they import that code but call none of it, and one call clears it. That covers the eval fixture, which has no `path:`. The VERIFY line gains `| N hollow`, and JSON `summary.hollow` lists the features. A hollow pass is never cached. Before this, the zero-case refund fixture in the evals got `PASS`, and `tests --strict` reported no problem. Only features whose checks are all `test:` and whose recipe has no `## Run` section are judged, because a `run:` check drives an app the measurement does not see. Cached passes, non-Python checks and modules with no function are not judged either. Measurement uses `sys.monitoring` on 3.12+: each code object reports its first start, then costs nothing. Older interpreters keep the `setprofile` hook.
- **Module-style test commands map to their files.** `python -m unittest test_refund`, `tests.test_refund.T.test_x` and `pytest test_x` now name `test_refund.py` and `tests/test_refund.py`. Before this, `run` listed the file as an orphan test and `tests` scanned none of its functions.
- **`challenge --auto` asks for less.** With no FILE and no `--diff`, it mutates the feature's `path:` files. It also runs without a `fail-signal:`, counting any failing check that is not a harness error as caught and saying so. The survey records no receipts, so this weakens nothing. A recorded `--mutation` challenge still needs a signal. Before this, `--auto` errored with "needs a FILE" even when `path:` named one, and in an eval it refused to run on a feature without a signal.

## 1.14.0 - 2026-10-20 - The helper decides when to swarm

- **`report` says what is left and who does it.** A `NEXT` line per unfinished feature (its step and the command), then `SWARM: solo | split | judge | done`. `split` means 3 or more open features: start helper agents, each with its own `VERIFY_AGENT`, each claiming with `swarm --claim`. `judge` means a feature needs `independent` verification by an agent that did not freeze it. `report --json` adds `next` and `swarm`. Plain `swarm` prints `SWARM-ADVICE:`, and `swarm --json` adds `advice`. The user and the calling agent no longer need to know when a swarm pays off.
- **SKILL.md: who does the work is the helper's call.** After recording checks, run `report` and follow its `SWARM:` line. With no way to start agents, work the list yourself and report `not_independent`. A second name for yourself does not count as a judge.

## 1.13.2 - 2026-10-20 - Survey maps files through the coverage map

- **`swarm --auto` and `review` read the recorded coverage map.** A file that a feature's check executed under `run --record-coverage` now belongs to that feature, so the survey scores it per feature instead of as `UNMAPPED`. A check like `python -m unittest test_app` names no product file, so before this a feature needed a `paths:` line to own the code it tests. Features with declared `paths:` also own files their checks executed. As with `run --affected`, the map is as fresh as its last recording.

## 1.13.1 - 2026-10-20 - Swarm survey judges each mutant once

- **`swarm --auto` no longer inflates `UNCOVERED`.** A feature that mapped none of the changed files used to get every changed file, so an unrelated feature reported `UNCOVERED` lines that another feature's checks catch. Now a feature surveys only the files it maps. A file no feature maps still goes to every feature, so it is still judged.
- **Repo-wide counts are per mutant.** The repo-wide `caught`/`survived`/`uncovered`/score, and the `SURVIVED`/`UNCOVERED` lines, judge each mutant once: caught if ANY feature catches it. `swarm.merge_mutants()` does the merge, which moved from `review` and is now shared by `review` and `swarm --auto`. The JSON adds `mutants` (merged) next to `results` (one row per feature run).
- **Per-feature scores count only mapped files.** Mutants of an unmapped file count repo-wide only and are listed as `UNMAPPED` (`unmapped` in JSON). A feature with no mapped file in the survey no longer appears per feature.

## 1.13.0 - 2026-10-20 - Review by proof

- **`verify.py review [--base REF]`.** It reviews a change, a PR or another agent's work, and its output is findings a person can re-run. High findings are where the change weakened its own proof: a test function that existed at the base is removed, newly skipped, has fewer assertions or can no longer fail (Python, JS/TS, Go, with renames paired). Also a check, fail-signal, feature or `require:` word dropped from VERIFY.md, or an oracle or check script edited alongside the code. Medium findings are where the change is not proven: `UNCOVERED` and `SURVIVED` changed lines, each with a `reproduce:` `challenge` command, `UNMAPPED` product files, and `NOT SURVEYED`. It reads only. Exit 0 clean, 1 findings, 2 cannot review. `--no-mutate` returns the static part in about 0.3 s on this repo. Mode doc: `references/review.md`.
- **Merged mutant verdicts.** The review counts a mutant as caught when any feature's check catches it. `swarm --auto` judges each feature on its own and falls back to every changed file for a feature that maps none, so an unrelated feature reports lines that another feature catches as `UNCOVERED`. `swarm --auto` itself is unchanged.
- **Internals.** `swarm.survey()` returns the survey summary, shared by `swarm --auto` and `review`. `tests_in_text()` audits file content and counts assertions per test.

## 1.12.0 - 2026-10-20 - Multi-agent swarms, zero-dep coverage, and anti-gaming

- **Multi-agent swarm coordinator (`verify.py swarm`).** `swarm` inspects `VERIFY.md` and `.verify-state.json` to classify every feature into its next required verification step (`map` -> `fix` -> `prove` -> `freeze` -> `challenge` -> `independent` -> `run` -> `done`). Agents with `VERIFY_AGENT=<name>` claim features atomically under the state lock (`swarm --claim [--role any|worker|judge] [--lease 600]`). Leases auto-advance as soon as the real receipt, baseline or strict pass lands in `.verify-state.json`, and `independent` / `judge` tasks are never routed to an agent in `frozen_by`. `swarm --auto [--diff [REF]] [--jobs N]` runs mutation surveys across every mapped feature in shared scratch lanes.
- **Peer-swarm `verified_by` independence.** When an agent `runner != freezer` passes a check under `--strict`, `verified_by` records `(agent, signature, tree)` in shared state. Two peer agents (`alpha` freezes A & verifies B; `beta` freezes B & verifies A) can now reach strict green without deadlocking or needing a third agent. Any edit to the tree or check invalidates `verified_by`.
- **Zero-file inline `challenge` and single-copy execution.** `verify.py challenge . --feature F --file <f> --before <a> --after <b> [--claim <c>]` runs a challenge without writing a JSON file into the checkout. When there is no `## Run` recipe, `challenge` copies the tree once, reuses the clean scratch tree in place, and runs only the target feature's checks on the mutated tree.
- **Trust & anti-gaming hardening.** `proven_by` and `challenge` now reject a `fail-signal:` that also appears in the check's passing output (`SIGNAL IN PASS`), preventing banner or test-name signals that print on every run. Manual Python challenges validate syntax and AST change, rejecting comment-only or syntax-error mutations (`CHALLENGE: invalid`). Failure and challenge receipts record `"agent"` provenance.
- **Zero-dependency stdlib Python coverage (`run --record-coverage`).** Replaced the external `coverage.py` dependency with a lightweight `sys.setprofile` hook in `sitecustomize.py`, so `--record-coverage` and coverage-based `--affected` work on every Python 3 interpreter out of the box, and the `CoverageMap` test suite now runs unconditionally.
- **Polyglot `tests [--strict]` and fresh bytecode.** `verify.py tests` now audits JS/TS (`test`/`it`) and Go (`func Test...`) test functions alongside Python for hollow (`no assertion`), exception-swallowing and skipped tests. `run_check` and `start_app` set `PYTHONDONTWRITEBYTECODE=1` by default so same-second same-size edits and mutations never execute stale `.pyc` files.

## 1.11.0 - 2026-10-20 - Harder to fool

- **`require: independent`.** `baseline` records which `VERIFY_AGENT` froze each check
  (`frozen_by`, shared state; a later baseline keeps the original freezer of an unchanged check).
  With `require: independent` in VERIFY.md, `run --strict` stays red with `NOT INDEPENDENT` for a
  check frozen by the agent whose run claims green, or by an unnamed agent. `report` lists the
  `not_independent` gap; run JSON counts it. Names are recorded, not authenticated.
- **`challenge --auto --diff [REF]`.** Mutates only lines added or changed since REF (default
  HEAD), uncommitted edits included. With no FILE (`--auto --diff`) it surveys every changed product
  file and skips tests, oracles and the recipe. It uses the same lanes and verdicts; JSON adds `diff`,
  `files` and a `file` per result. A change with no mutable line exits 2.
- **Coverage-based `--affected`.** With coverage.py importable, `run --record-coverage` records the
  repo files each check executes, and `--affected` selects by that map as well as by file names
  (which miss imported helpers). This stays optional: without coverage.py the run says so and
  proceeds. Only files with executed lines count: with `source =`, coverage.py also lists files it
  never ran. Tested against coverage.py 7.16.2. Its two tests skip when coverage.py is not
  importable.
- **Fix: `--affected` can no longer make `--strict` green.** 1.10 exited 0 for
  `run --affected --strict` on a selection. Now it exits 1 with `SELECTED`, including when nothing
  changed. Changed-file lists no longer include verify-loop's own state and cache files.

## 1.10.0 - 2026-10-20 - A fast, shared inner loop

Timings are warm medians on this Windows machine (Python 3.13). The test repo is 60 MB of git:
1,500 small source files and twelve 5 MB binaries.

- **Fast tree signature.** A non-strict `run` and `watch` fingerprint the tree from a stat cache.
  A file whose size, mtime and (on POSIX) ctime are unchanged since it was last hashed is not read
  again, as git's index works. `--strict`, `status`, `ci` and `challenge` still read every byte.
  Both ways give the same signature for honest stat data, so `status` can judge a fast-recorded
  run. Limit: an edit that restores size and timestamps goes unseen by the fast path until a full
  pass. Files changed in the last 2 s are always re-read. The signature itself went from 0.30 s to
  0.011 s on the warm path. Warm `run` went from 0.340 s to 0.208 s; the rest is Python startup
  and the check. `run --strict` went from 0.342 s to 0.319 s and `status` from 0.157 s to 0.150 s.
  The cache stays out of the git signature: no blob hashes, because `core.autocrlf` and ignored
  files would make git's view and a full read disagree.
- **Shared result cache.** `run` reuses a pass any agent or worktree already proved for the same
  command on the same content. Text shows `[CACHED: proved <time> by <agent>]` and a
  `CACHED  n check(s) reused` line; `--json` adds `cached` per result and in the summary. Only
  passes from runs whose tree did not move are kept. A pass recorded under the fast signature
  never satisfies `--strict`, which reuses only full-signature passes. There is no caching with a
  `## Run` recipe or `--stress`, and `run --no-cache` opts out. The cache sits in Git's common
  directory (`.git/verify-loop/`), shared by every worktree, with an atomic, locked write, or in
  `.verify-state-cache/` outside Git. Three 1 s checks: rerun on unchanged content 3.36 s to
  0.17 s; strict rerun 3.61 s to 0.38 s; a second worktree on the same content 3.36 s to 0.16 s.
  Challenge, `--auto` lanes and `ci` never use it.
- **Slots and ports for `--jobs`.** Every check runs with `VERIFY_SLOT` (0..N-1, never shared by
  two running checks) and a fresh free `VERIFY_PORT`, so checks that start their own app can run
  in parallel. Four checks that each start an HTTP server: 6.09 s serially (1.9.0 with `--jobs 4`
  had 3 of 4 fail on the shared port), 1.67 s with `--jobs 4`, all passing. The pattern is
  documented in `references/helpers.md`.
- The tree signature now covers `fixtures/` folders: a fixture is an input, so editing one makes
  `status` stale and misses the cache. A worktree's `.git` file is left out. The signature format
  changed, so a green `status` recorded by 1.9.0 reads `stale` once; run again.

## 1.9.0 - 2026-10-20 - Faster, more honest mutation surveys

- `challenge --auto` copies the tree once per lane instead of twice per mutant. Each lane runs the
  unmutated checks once, then writes every mutant in place, judges it against the selected feature's
  checks only, and reverts it. A lane whose checks leave other files changed is recopied first. On a
  60 MB repo with one check, 6 mutants went from 203 s to 18.6 s.
- `challenge --auto --jobs N` judges mutants in N parallel lanes. With a 1 s check, 6 mutants went
  from 13.1 s (1.8.0) to 8.7 s with one lane and 3.4 s with `--jobs 6`. A `## Run` recipe forces one
  lane. Where copying the tree dominates, more lanes do not help.
- Duplicate mutants are dropped: two operators that produce the same line (`zero-to-one` and
  `int-off-by-one` on `0`) count once, and so does a Python mutant whose syntax tree is unchanged.
- A survivor on a line no check executes is now `UNCOVERED`, found by a probe that aborts before
  that line and still passes. It counts against the score like a survivor, but it names a missing
  check rather than a weak one. JSON adds `uncovered`, `jobs` and `copies`.
- `run` without a `## Run` recipe hashes the checks twice (before and after) instead of three times.
- `challenge.py` exposes `prepare`, `mutable_target`, `judge` and `copy_repo`, so `--mutation` and
  `--auto` judge mutants by the same rules.

## 1.8.0 - 2026-10-20 - Many agents, one checkout

- State writes are atomic: each save goes to a temp file and replaces `.verify-state.json` whole.
  Before, a reader racing six writers saw a half-written file 38 times in 6 seconds.
- Each save takes a short lock (`.verify-state.lock`), re-reads the file and merges. A key the
  saving process did not change keeps what is on disk, receipts are merged per check and
  re-baselines are appended, so a stale save no longer reverts another agent's baseline or drops
  its receipts. Six processes saving 25 receipts each now keep all 150.
- `VERIFY_AGENT=<name>` gives an agent its own loop memory in `.verify-state.<name>.json`: last
  run, NEWLY RED/SAME FAILURE, rounds, scope, doctor and `status`/`report`. The baseline,
  re-baselines and rejection receipts stay in `.verify-state.json` for every agent, so a new name
  cannot escape a freeze and one agent's proof that a check fails counts for all. A bad name exits 2.
- Every `.verify-state*` file is left out of the tree signature, scope, challenge copies and CI
  inputs, so one agent's save does not make another's green stale. Gitignore `.verify-state*`.
- `challenge` no longer calls itself inconclusive because another agent added a receipt meanwhile.

## 1.7.0 - 2026-10-20 - Parallel checks

- `verify.py run --jobs N` runs up to N checks at once and reports them in recipe order, so
  output, loop memory and verdict match a serial run. On a 20-check repo, `--jobs 8` cut a run
  from 7.6s to 1.6s; check execution was 93% of run time. Default stays 1: checks that share an
  app, port or files can collide. Documented in SKILL.md and `references/helpers.md`.

## 1.6.0 - 2026-10-19 - Built for stronger agents

- `require: challenge` (a top-level VERIFY.md line, written by `init`, frozen by `baseline`) keeps
  `run --strict` red with `UNCHALLENGED` until a `challenge` mutation is caught for the current
  checks. `report` lists it under the new `unchallenged` gap.
- `.verify-state.json` is sealed with a content hash. A hand-edited file reads as `STATE FORGED`
  on run and `tampered` on status until it is deleted. Existing unsealed state files read as
  tampered once: delete them and verify again.
- SKILL.md: done includes a caught challenge, the check-strength ladder has no top rung, and a new
  section treats the checker as foolable (separate judge from worker, freeze before building,
  prefer third-party evidence). The build-identity steps are summarized in the project recipe.

## 1.5.0 - 2026-10-19 - A frozen check cannot be quietly re-frozen

- `verify.py baseline` refuses (exit 1, `BASELINE REFUSED`) when a frozen test or oracle file
  changed, a check command was removed or edited, or a feature's `fail-signal:` changed, unless
  `--reviewed-by <name>` and `--reason <why>` are given. Added checks, test files, oracles and
  features, and `## Run` repairs, still freeze without review.
- Each reviewed re-baseline is recorded in `.verify-state.json` (`rebaselines`: who, why, what,
  HEAD). `status` prints `RE-BASELINED` lines and `report` lists `gaps.rebaselined` until the change
  is committed.
- SKILL.md, triage, answer and VERIFY_FORMAT document the rule and its limit: local state is
  editable, so CI and review rules stay the independent guard.

## 1.4.1 - 2026-10-19 - Docs match what ships

- New `references/helpers.md` documents `loop`, `watch`, `triage`, `contract`, the scaffolds and
  `--stress`/`--quarantine`, including when an agent may quarantine a check.
- `loop` is described as rerun-and-triage (it makes no edits); `watch` is shown with `--max-runs`
  so an agent's shell does not block.
- `ci.md` drops its table of skills that no longer ship and says the CI example lives in the
  source repo, not the installed skill. `VERIFY_FORMAT.md` no longer names the missing
  `features.py`. README drops its `correctness-gate`/`wire-check` note.

## 1.4.0 - 2026-10-19 - One answer reference

- `references/handoff.md` is now `references/answer.md`: one contract for every caller, what they
  pass and what comes back. The table of caller skills that no longer ship is gone, and SKILL.md
  drops its separate handoff row.

## 1.3.0 - 2026-10-19 - Sharper SKILL.md

- Rewrote `SKILL.md` around check quality: what a good check is, the loop, and what to look for
  before saying done. Helper commands are listed in one line instead of explained; detail stays in
  `references/`. Dropped pointers to skills that are no longer shipped.

## 1.2.0 - 2026-10-19 - Maintain mode

- Maintain mode (`references/maintain.md`) is a periodic pass over a project verify skill. It
  has three outcomes: clean, changed or blocked. Its edit scope keeps frozen checks behind a
  person's review. The pass reads every feature from source, runs a live pass over every
  feature, triages drift into map drift, harness gaps and product gaps, and ends on
  `run --strict` + `report`.
- The new `verify.py maintain` is a read-only audit. Per feature it reports `map`, `re-prove`,
  `fix`, `re-drive` or `drive`. It also reports skill-check shape problems, checks changed since
  the baseline, and changed files that no feature claims. Churn counts from a committed
  `last-maintained: <sha>` line in `features/README.md` (or `--since REF`). A check input that
  matches the baseline does not count as churn.
- Create mode now records `last-maintained:`, and generated skills point to maintain mode.

## 1.1.0 - 2026-10-19 - One way in, one answer, create mode

- verify-loop is no longer manual-only. The new description lets users, skills and agents call it
  to verify a change, prove a task is done, or create a project verify skill. SKILL.md gains a
  "How to call me" section.
- One answer for every caller, documented in `references/handoff.md`: the verdict
  (green/red/partial/stale/unverified), the `VERIFY:` line, the observed rejections, what passed
  and the gaps. The new `verify.py report` prints it. `status --json` and `report --json` now
  return `verdict`, `verify_line`, `rejections`, `passed` and `gaps`, and keep the earlier fields.
  `run --json` carries `verify_line`, and the last whole run's line is kept in state.
- Create mode (`references/create.md`) generates a project `.claude/skills/verify/` skill named
  `verify` (Launch, Doctor, Drive, Evidence, Cleanup, Helpers, Verdict) plus a feature map. Each
  feature is tied to a VERIFY.md section with a `fail-signal:` and a `fail-proof:`. The new
  `verify.py scaffold-skill` drafts it from the detected stack, and `verify.py skill-check` lints
  it. `examples/verify-create/` is a proven run. Ideas come from pstack's
  `create-verification-skill` (MIT, see `NOTICE`).

## 1.0.0 - 2026-10-19 - Verify Loop on its own

- Cut from top-tier-engineer 4.66.0, keeping only the `verify-loop` skill, its scripts, its unit
  tests and the `examples/verify-ci` workflow. Other skills, agents, hooks, the eval harness and
  the project docs are removed. The plugin is renamed `verify-loop`.
