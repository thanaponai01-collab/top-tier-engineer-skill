# Changelog

## 4.47.0 - 2026-10-03 - optional workflows by default

- Default hook manifest is empty. The previous four hooks remain in `hooks/optional.json` for explicit opt-in.
- `drive` remains the entry point for orchestrating skills; ordinary work needs no skill calls or skip justification.
- Optional philosophy no longer requires `verify-loop` beyond typos or repeated permission for authorized actions. Routing hints are advisory.
- Updated hook tests cover the inactive default and the optional manifest. Existing skill workflows are unchanged.

- Merged architecture dependency-map and slim-skill branches; preserved optional hooks and workflows.

## 4.46.0 — 2026-09-30 — arch-design: one purpose again, 231 lines to 98

- **`arch-design` `SKILL.md` cut back to its job:** improve, redesign a part, or design new backend
  structure, using a short list of engineering techniques (one owner per job, dependencies one way,
  logic apart from I/O, small interfaces, clear boundaries, data model first, no structure nobody
  needs). It picks improve / replace-a-part / design-new first and says which; replacement is one
  part at a time behind a stable interface and needs the user's yes. Answer is a ranked list in chat.
- **Moved out of the main flow:** the graph and history instruments, and the optional
  `docs/arch-design.md` format with its `check`, now live in `references/instruments.md`. The
  scripts are unchanged.
- **New test** caps `SKILL.md` at 110 lines, so a new section has to displace an old one.
- **Measured.** Suite 277 green. `arch-design-no-new-store`, with-skill n=2: 0/2 pass (2/3 and 1/3
  items), $0.18 a run, about half the old skill's cost. Still missing: naming what a separate new
  datastore would cost. Improve-vs-replace and design-new behavior are suspected, not measured.

## 4.45.0 — 2026-09-30 — arch-design: `dep-map.py`, See / Judge / Shape

- **New `dep-map.py` (arch-design).** Reads the import graph that `latent-audit`'s `graph-audit.py`
  now writes with `--edges FILE`, so the graph is built once, in one place, and nothing here
  re-parses imports. Reports import cycles (with `file:line`), the most-imported modules with their
  instability, modules whose every function only forwards its own arguments, Protocol/ABC seams by
  how many classes implement each (one is a guess, two a fact), and modules that import a network,
  database or process library. `--cochange` (from `change-map.py --json`) adds which co-changing
  file pairs have no import edge. Leads, not verdicts. Python only, stdlib only.
- **`arch-design` `SKILL.md` rewritten** as See → Judge → Shape (was six phases). New: run the
  graph and the history before reading, judge modules by what they import and who imports them
  (a module imported by many that imports nothing is stable, not a defect), count seams before
  calling one over-built, reuse the repo's existing owner before adding a second, and say how to
  test across a seam by what is on the other side. The move block and file format are unchanged.
- **`arch-design.py check` works outside a git repo.** It treated `docs/` as the root and rejected
  every path, and reported the pinned commit as stale. Both baseline runs on a fixture hit it. With
  no git the root is the folder above `docs/` and staleness is skipped.
- **Proven.** 9 tests for `dep-map.py` (planted patterns with a decoy each, and the 40-module eval
  fixture giving exactly the planted answer); breaking the tool four ways turned a test red each
  time, after one surviving break got its own test. Tests written first for `--edges` and for the
  `check` fix. Suite: 276 green.
- **New eval case `arch-design-graph-shape`** (40 modules: a three-module cycle, a network call in
  the price calculation, a pass-through service; decoys: a two-adapter payment seam, a stable
  utility imported by 16 modules). **A plain agent passes it** (2 of 2, and 2 of 2 with the previous
  skill), as it did an earlier 9-file version: at this size the agent reads everything, so the case
  does not show the skill helping. It stays as the fixture for `dep-map.py`'s tests. Evidence in
  `evals/results/2026-09-30-arch-design-*`.
- **Measured, new skill, existing cases (2 tries each, claude-sonnet-5-5).** `graph-shape` 2/2,
  `one-owner` 2/2, `verify-caller-count` 2/2. Cost did not fall: $0.33–0.34 per graph-shape run vs
  $0.36 before, and report length is unchanged; `SKILL.md` is 224 lines (was 236), not the ~150
  aimed for. Agents ran `dep-map.py` in 3 of 8 runs, all where the repo was big enough to need it.
- **Known regression, shipped anyway.** `arch-design-no-new-store` passes 0 of 10 runs with the new
  skill against 3 of 6 with the old one. The new text pulled agents toward audit findings on the
  existing code and away from the design decision. Adding "reuse before you add" and restoring the
  "plugin system with one plugin" line moved every run from 0–1 to 2 of 3 planted items, but all
  four still miss the third: none compares a separate datastore, so none names its cost. Not fixed.
  Next step if wanted: make "the store the app already has" a mandatory option in every
  where-does-new-data-live decision.
- **Not done.** A separate module-design skill (its case has to be something a plain agent does
  not already pass), and a refreshed `RESULTS.md` (a partial run would drop the other rows).
- **A fixture cannot carry git history.** `run.py` copies only `fixture/`, so `change-map.py` and the
  co-change join remain unmeasured by any eval.

## 4.44.0 — 2026-09-29 — verify-loop: `verify.py tests`, every test mapped to a feature

- **New `verify.py tests [--strict]`.** `verify.py run` mapped test *files* to features, so a file
  with forty tests was one row and a hollow test hid inside a "verified" feature. `tests` goes down
  to the function: every test listed under the feature whose command names its file, and each one
  flagged when it has no assertion (directly or through a helper in the same file), catches its
  exception and passes either way, is skipped, or sits in a file no feature names. Static (it parses
  and runs nothing), Python only; JS/TS test files are counted but not itemised. Ends with
  `TESTS: n tests | m mapped | k unmapped | h without an assertion or a way to fail | s skipped`.
  `--strict` exits 1 on any flagged or unmapped test; no `VERIFY.md` exits 2. The existing `VERIFY:`
  summary line and `run` output are unchanged. `SKILL.md` step 7 says to run it after adding tests.
- **Proven.** Six new tests in `tests/test_verify.py`, written first and red before the code, with
  decoys that must not be flagged (a test asserting through a helper, `assertRaises`, a bare
  pytest-style `assert`). Breaking the detection six ways (helper calls not counted, swallow check
  off, skip check off, `--strict` ignored, every file under every feature, bare `assert` ignored)
  turned a test red each time. On a probe suite the tool flagged the two assertion-free tests in a
  file that `run` reported as a verified feature.
- **Measured, existing `verify-loop` cases (3 tries per side, claude-opus-5-5).** With the plugin 10
  of 15 passed, without it 3 of 15, so the change did not regress the skill; evidence in
  `evals/results/2026-09-29-1859/`. Per case, with vs without: `check-is-wrong` 3 vs 0,
  `make-it-verified` 3 vs 0, `check-cannot-fail` 1 vs 0, `green-with-unverified` 0 vs 0,
  `fake-check-and-decoy` 3 vs 3. The two low rows miss the same item on both sides (no fail-proof
  recorded), so they predate this change.
- **Not measured.** No run called `verify.py tests`: none of these cases is about test volume, so
  they say nothing about whether an agent reaches for it. `RESULTS.md` was not regenerated (a
  five-case run would drop the other rows).
- **Considered and not built.** A `test-audit` skill (break the code, read the assertions) and two
  write-time cases (add tests to a 3-function module and to a 17-function package). A plain agent
  already audits well when asked (3 of 3), and already writes tests that catch every planted break
  (6 of 6 on the small module, 3 of 3 on the package, 24 breaks); it also found and reported real
  bugs in the fixture. No gap, so no skill. One caveat: the with-plugin agents left the tests that
  exposed those bugs failing where plain agents marked them `expectedFailure`, which the case's
  "green on correct code" check scored as a failure, so its with-plugin results were not usable.

## 4.43.0 — 2026-09-29 — `plan-work`, and the nine checkpoints named

- **New skill `plan-work`: the Plan checkpoint.** Every `drive` playbook went from framing or design
  straight to building, so nobody owned cutting the work into pieces, ordering them, and saying
  which can safely run at the same time. It writes `PLAN.md`: slices, each with a check whose
  expected value is worked out beforehand; the "can run together" mark only after opening the shared
  code; and, when work is handed to other agents, a brief that stands alone, a rerun of each report's
  check, and the whole exit check after every merge.
- **The Relay, in `pick-skill`.** The nine checkpoints (Orient, Frame, Design, Plan, Build, Prove,
  Review, Ship, Watch), the one skill that owns each, and the file each leaves for the next. Every
  checkpoint but Plan already had an owner; this made that visible. `drive`, `build-discipline`, the
  README and the flows table point at `plan-work` where it belongs.
- **Measured, new case `plan-work-shared-function-and-decoy`** (3 tries per side, claude-opus-5-5):
  without the skill 0 of 3, with it 3 of 3. Evidence in `evals/results/2026-09-29-0815/`.
- **What the case showed about the baseline.** A plain agent already found the collision (discount
  and tax-exempt both rewrite `total()`) and already saw the export could run alongside, 3 of 3. It
  failed all three on one thing: no piece came with a command and an expected result. So the proven
  gain of this skill is the per-slice check; the parallel-safety steps are written down but were not
  what separated the sides.
- **Not measured.** Handing slices to real subagents and merging them back (steps 6 and 7) is not
  exercised by the case, which only plans. The new routing row (`evals/routing.json`) and the new
  `route-hint` rule are covered by `evals/route.py` (34 of 34) but `route_live.py` was not re-run,
  so nothing shows the agent now picks `plan-work` unprompted. `RESULTS.md` and `ROUTING.md` were
  not regenerated (single-case run).
- **Considered and not built.** A "land the change" skill (commit and PR packaging): a plain agent
  given a working tree with the fix, an unrelated edit, a leftover debug line and a fake secret
  committed only the fix and its test, 3 of 3, left the rest out and said so. No gap, so no skill.
- **Not fixed here, found on the way.** `evals/ROUTING.md` (2026-09-27) has the agent opening the
  right skill on 17 of 32 requests, and `RESULTS.md` has only 1 of 6 tries following the `drive`
  playbook step by step. Skills at every checkpoint do nothing if they are not opened. `marketplace.json`
  still says "Twenty-five" skills.

## 4.42.2 — 2026-09-28 — `project-setup` and `onboard-system` say which is which; evals run on Windows

- **The two descriptions now draw the line.** `project-setup` says it is only the checks and the
  pointer, and that `onboard-system` runs it; `onboard-system` says it runs `project-setup` first and
  that `project-setup` alone is for when only the checks are wanted.
- **New routing case for `onboard-system`** in `evals/routing.json` ("I've never seen this codebase
  before…"). Run live, 3 tries each: it picked `onboard-system` 3 of 3, and the existing
  `project-setup` case picked `project-setup` 3 of 3.
- **Evals no longer die instantly on Windows.** `evals/agent.py`'s environment allow-list dropped
  `SystemRoot`, so every headless agent call exited in 0.1s with "Bun needs this set" and
  `route_live.py` reported `0 of N right`. It now keeps `SystemRoot`, `USERPROFILE`, `APPDATA` and the
  other variables Windows needs.
- **Not measured.** There was no run before the description edits, and `onboard-system` was already
  hinted by the `route-hint` hook, so this does not show the wording changed a pick. `ROUTING.md` was
  not regenerated. `route_live.py` still crashes printing `←` on a cp1252 console unless
  `PYTHONUTF8=1` is set, and the runner still discards the child's stderr.

## 4.42.1 — 2026-09-28 — first contact and resume no longer dead-end

- **`recall` reads `docs/architecture.md`.** `onboard-system` writes that file, but `recall` only
  looked for `docs/arch-design.md`, so the resume skill never saw the output of the skill that
  feeds it.
- **`recall` hands first contact to `onboard-system`.** On a repo it has never seen, with no
  `VERIFY.md`, `FEATURES.md` or `WHY.md`, it used to stop at "nothing recorded". It now says this is
  first contact and names the skill to run.
- **`drive` routes "unfamiliar codebase / get me up to speed" to `onboard-system`.** No row matched
  that goal before; only `project-setup` was listed for a new repo.
- **`project-setup`'s pointer block mentions `recall`,** so a fresh session is told the resume
  skill exists.
- **Not measured.** The unit tests pass, but `recall`, `project-setup` and `drive` have no eval case
  covering these routes, so nothing has shown the new wording changes what an agent does.

## 4.42.0 — 2026-09-28 — verify-loop: repairing a check that never ran, and evals that grade what the agent left behind

- **`verify-loop` step 4 now covers a check that cannot fail.** A check that runs nothing (loads no
  cases, mocks the thing it tests, asserts nothing) is broken machinery, and repairing it before the
  freeze is part of building the check, not an edit to make it pass. What the check *expects* is left
  as it was, since an expected value comes from the claim or the spec, never from the code. The agent
  proves the repaired check can fail, freezes it with `verify.py baseline`, and lists the check files
  it changed so a person can review them.
- **Step 6 is narrowed to say what it always meant:** a check you believe is wrong about what it
  *expects* is a finding, not an edit. Repairing a check that never really ran is step 4; changing
  what a check expects so it passes is step 6. The two steps used to read as a conflict for an
  existing broken check with no baseline. Step 3 also notes `verify.py` works in any folder, git or
  not.
- **Measured, small samples (3 per condition, 5 for the case-C regression check).** Agents reading
  the original text froze the baseline in 0 of 3 runs, and only 1 of 3 ran `verify.py` at all; with
  the new text 3 of 3 ran it and froze the baseline, with `verify.py status` green. Reading the
  original text from disk instead of through the Skill tool changed nothing, so the difference is the
  wording. The case where the right move is to stop still held: 5 of 5 left every file untouched.
- **Four new eval cases for `verify-loop`.** `verify-loop-check-cannot-fail` (a test that quietly
  loops over nothing), `verify-loop-green-with-unverified` (a feature no check covers),
  `verify-loop-check-is-wrong` (a stale test over correct code) and `verify-loop-make-it-verified`
  (the same vacuous test, but the ask is to get it verified, graded on the finished repo).
- **`evals/grade.py` can grade actions, not only reports.** A case's `workdir` block is checked
  against the copy of `fixture/` the agent worked in: `edits_allowed` fails any change outside the
  named files, `must_contain` requires a regex to match a file, and `replays` re-runs the copy's own
  tests against a known-broken and a known-correct version of the code, so a check is judged by
  whether it can tell them apart. A `must_contain` or `replays` item may carry `"gate": false`, shown
  as a note without deciding the verdict. Without `--workdir` a case that grades actions will not pass. `tests/` also
  breaks a finished copy the ways a shortcut would (delete the test, make it always fail, empty the
  data, write the proof line without fixing the check, edit the check to pass) and requires each to
  fail on a named check.
- **The real-agent runner judges the finished copy too.** Each new case ships the `prompt-plain.md`
  the runner now requires, and `evals/run.py` hands a case's `workdir` rules the agent's finished
  copy, so a real-agent run of an action-graded case cannot pass on its report alone. A `--rescore`
  keeps the saved working-copy verdict, since the scratch folder is gone by then. Without this the
  runner would have graded those cases on words while `grade.py` graded them on actions.

## 4.41.5 — 2026-09-28 — the evals run real agents, with the skills and without

Until now the eval cases had an answer key but had never been sat by an agent. Now they are, and the
score is in `evals/RESULTS.md`.

- **`evals/run.py`** gives every case to a real agent several times, with this plugin and without
  it (plain Claude Code, the task in plain words from the new `prompt-plain.md`), and writes a
  with-vs-without scorecard. The agent only ever sees `fixture/`; a run that reaches for the answer
  key is discarded.
- **Grading what the agent did, not only what it wrote.** Each case's `actions` block is checked
  against the transcript: report-only tasks leave code alone, the repro runs *before* the first
  edit, the deploy script never fires, `drive` opens its playbook's skills in order, and after the
  run the fix is real on disk and production untouched.
- **`evals/judge.py` grades reports on meaning.** A separate model, blind to which side wrote the
  report, credits a finding only with a quote that is really in the report. It judges all 33
  reference reports correctly (`--calibrate`). The phrase grader is kept alongside for comparison.
- **`evals/route_live.py`** checks whether the agent picks the right skill by itself on 32 requests
  that name none, and what the `route-hint` hook suggested. Table in `evals/ROUTING.md`. (Renamed
  from `route.py` to leave room for the free, static `route-hint` regression check of the same name.)
- **Two cases for the riskiest skills:** `drive-overnight-parks-the-deploy` (a README telling an
  unattended agent to run a deploy that emails every customer) and
  `safe-release-migration-loses-data` (a migration that silently drops data behind a green suite).
- **A new skill lands with an eval case.** `evals/uncovered.txt` lists the 20 older skills without
  one; it may only shrink, and the suite fails if a skill is in neither place.
- Checker fixes found by reading real runs: a deploy command written into notes is not running it;
  "one caller-less" is not "one caller"; "one-implementation" counts; inside one shell command, the
  order of run and edit decides which came first. Each is now a test.
- Checks only the side with skills can be asked (did `drive` open each step's skill?) are scored
  apart from the with-vs-without table, so they can't tilt it.
- Saved evidence carries no email address or git user name; raw transcripts stay local.
- First scorecard: 6 tries per side on 11 cases. The skill clearly helps on 6, makes no clear difference
  on 4, and hurts on 1 (`latent-audit` hedges on the one file that really is dead). On their own, agents
  rarely open a skill for everyday requests (`evals/ROUTING.md`, 17 of 32).
- `drive-bug-through-skills` no longer grades whether the report *names* skills; it checks from
  the transcript that they were opened, in order.
- README: the skill count said twenty-five; there are twenty-nine.

## 4.41.4 — 2026-09-28 — five new eval cases for the judgment-call skills

- **New eval cases**, one each for `verify-loop`, `perf-optimize`, `threat-model`, `senior-review`
  and `safe-release` — the skills that make an objective judgment call over a script's yes/no, and
  so are the ones most likely to be fooled by a decoy next to the real problem:
  - `verify-loop-fake-check-and-decoy` — a test that recomputes its own expected value and never
    calls the function under test, next to a one-line test that looks just as trivial but is real.
  - `perf-optimize-n-plus-one-and-decoy` — a query-per-customer loop that's a finding even though
    each query is indexed, next to an `ORDER BY ... LIMIT` that looks like a full sort but isn't.
  - `threat-model-client-role-and-decoy` — an authorization check that trusts a client-supplied
    `role` field over the session, next to a catalog endpoint with no auth that's intentionally
    public per its README.
  - `senior-review-oversell-and-decoy` — `reserve_stock` oversells with no qty validation, proven by
    running it, next to a lock-free global dict that looks unsafe but has nothing here to prove a
    race against (single-process CLI).
  - `safe-release-combined-migration-and-decoy` — one migration that expands, backfills and drops a
    column together with an untested "revert the commit" rollback claim, next to a second migration
    in the same release that really is safe as it stands.
  Each ships `prompt.md`, a fixture that runs, `expect.json` (planted + traps) and the three
  reference reports (`good`, `good-alt`, `bad`) `tests/test_evals.py` checks the case against.

## 4.41.3 — 2026-09-28 — route-hint closes the gaps a real routing eval found

- **New `evals/route.py`.** Scores `route-hint.py`'s `suggest()` against a batch of real prompts,
  including several written to expose overlap between skills whose descriptions look alike from
  outside — `arch-design` vs `structure-gate`, the `agent-*` family against each other, "done" the
  goal-word vs "done" the finished-work-word. `python evals/route.py`; exit 0 only if every case
  passes.
- **`route-hint.py` gains rules for `arch-design`, `feature-map`, `verify-loop`, `agent-evals`,
  `agent-prove`, `agent-trace`, `agent-release`, `problem-framing` and `drive`** — nine skills that
  previously had no rule at all, so a prompt clearly asking for one routed to silence instead.
  `BROKEN` now also catches "timing out" / "timeouts", which were symptom words with nowhere to go.
- Fixed a false-negative the new `drive` name introduced: the "did they already name a skill"
  check was plain substring matching, so `"drive"` matched inside `"driven"` and silenced routing
  for that prompt. It now matches skill names on word boundaries.
- Baseline on the new eval was 20 of 32; all 32 pass after these rules.

## 4.41.2 — 2026-09-28 — direct tests for structure_opacity

- **New `tests/test_structure_opacity.py`.** `structure-gate`'s opacity/shape module
  (`structure_opacity.py`) was only exercised indirectly, through `structure-report.py`'s CLI in
  `test_structure_report.py`. Adds direct unit tests for `contiguous_spans`, `python_opaque_lines`,
  `shape_stats`, `is_code_shaped`, `looks_like`, and `measure`, so a change to one of those functions
  fails at its own test instead of surfacing as an unexplained shift in someone else's CLI assertion.

## 4.41.1 — 2026-09-28 — verify-loop: stop leaving the started app as a zombie

- **Fixed `start_app` in `verify-loop`'s `scripts/verify.py`.** On a shell that forks a real
  child for a single command instead of exec-replacing itself, `Popen`'s `proc.pid` named the
  shell, not the app — so `stop_app`'s `os.killpg` + `proc.wait()` killed the app but only ever
  reaped the shell, leaving the app an orphaned zombie `stop_app` could never confirm was gone.
  `start_app` now runs the command as `exec {cmd}` (POSIX only) so the shell always replaces
  itself with the real process; `proc.pid` is then guaranteed to be the app itself.

## 4.41.0 — 2026-09-27 — onboard-system: the paved path for first contact with a codebase

- **New `onboard-system` skill.** First contact with an unfamiliar codebase: runs `project-setup`,
  `feature-map`, `arch-map` and `code-history` in the order that lets each one use the last one's
  output (setup → what it has → how it's shaped → why), then proves the resulting picture with an
  `explain` overview checked against a real prediction. Ends with `VERIFY.md`, `FEATURES.md`,
  `docs/architecture.md` and `WHY.md` all on disk, so the next session or agent finds the whole
  picture instead of re-deriving it.
- `project-setup`'s `CLAUDE.md` pointer block now also names `docs/architecture.md` / `arch-map`,
  `WHY.md` / `code-history`, `debug-protocol` and `explain`, and points a fresh project with none of
  those files at `onboard-system` to build the full set in one pass. It previously mentioned only
  `VERIFY.md`, `FEATURES.md` and `code-history`.
- `route-hint.py`'s "onboarding onto X" phrasing now routes to `onboard-system` instead of `explain`
  — that phrase means the whole first-contact pass, not one paced explanation. `pick-skill`'s table
  gained the matching row.

## 4.40.0 — 2026-09-27 — agent-drift: catch a live agent slipping after launch

- **New `agent-drift` skill.** Turns `agent-release`'s three post-launch bullets (sample and grade,
  file failures as tasks, watch for drift) into the actual mechanics: pull the frozen `agent-prove`
  baseline, sample live traffic on a named schedule against a noise band (not a bare "it felt off"),
  root-cause an unpinned model/prompt change before anything else, and file every real drop as a task
  in `agent-evals`'s set before waiting on a fix.
- Hands off to `agent-prove` to confirm a regression against the bar, `agent-release` to roll back or
  throttle, `agent-trace` to pin the exact divergent step in a bad live sample. Closes the gap where
  monitoring a shipped agent had a checklist but no method for telling real drift from noise.

## 4.39.0 — 2026-09-27 — the tool surface gets designed before the agent does

- **New `agent-design` skill.** Before any agent code or eval exists: name the loop shape (one agent or
  an orchestrator, one owner per one-way action), list every tool with its reversibility tier and what
  it hands back into the agent's context (marking tools that return content an attacker could have
  shaped), decide the context/memory boundary, and write the whole thing to `docs/agent-design.md`.
  Closes the gap where `agent-evals` step 1 ("name the claim") had nowhere agent-specific to point for
  the must-refuse list, and pointed at generic `problem-framing` instead.
- `agent-evals` step 1 now reads the must-refuse list from `agent-design`'s tool contract when one
  exists, falling back to `problem-framing` → `agent-design` when neither the claim nor a contract can
  be said.
- `threat-model`'s Abuse phase gains an **agent tool surface** bullet: read the tool contract from
  `agent-design` (or list the tools by hand), test the untrusted-content tools for prompt injection and
  the one-way tools for reach-without-grounds and repeat-on-retry. `agent-prove` runs the resulting
  cases as tasks that must pass before release.
- `agent-release` step 8 (watch for drift) now runs on the same named schedule and owner as step 6
  instead of being an unscheduled bullet, and names the threshold that pages someone.
- `pick-skill` and the README list `agent-design`; `route-hint.py`'s skill list knows the name (no new
  routing rule — reached by name, `pick-skill`, or `agent-evals`'s fallback, same as the other three
  `agent-*` skills).

## 4.38.0 — 2026-09-27 — agent-trace: name where one agent run went wrong

- **New `agent-trace` skill.** Given one agent run's transcript (tool calls, results, reasoning),
  walks it step by step and names the first step where it diverged from what was wanted, plus the
  cause category at that step. Traces only — no fixing, no rate over many runs, no grader judgment.
- Hands off to `debug-protocol`/`build-discipline` for a fix, `agent-prove` for whether it's a
  pattern, `agent-evals` if the task or grader itself looks wrong. Closes the gap where `agent-prove`
  step 3 ("read the failures") and `debug-protocol` (code-only) had no single-run agent tracer to
  call.

## 4.37.0 — 2026-09-27 — arch-design verifies itself before handing off

- **New `## 6. Verify` step** in `arch-design`, between Move and Deliver: re-derive every Strong
  finding's and move's numbers with the same tools rather than re-reading the notes that produced
  them, then send each Strong finding and one-way door to a fresh subagent that is told the fact to
  check but never the conclusion it's supposed to reach — the run that found something is the worst
  judge of whether it's still true.
- `arch-design` no longer names `issue-handoff`, sets no `moves filed` status, and makes no claim
  about what happens to its output after `check` passes — that's the next skill's call, not this
  one's. `status` is now `open | landed`; `arch-design.py check` enforces the narrower set.

## 4.36.0 — 2026-09-27 — the map carries the move numbers

- `arch-design` hands `arch-map` the Change view whenever there are moves (not only "if asked"),
  with each move's number and a `move | what | cost | effort` table.
- `arch-map` marks each box or arrow with its `Move N`, so a reader approves moves from the picture.

## 4.35.0 — 2026-09-27 — every skill tuned to run cold as an agent

- **Stop rules and budgets** added where a run could loop: `agent-evals`, `agent-prove` (spend
  ceiling), `arch-design`, `build-discipline`, `code-history`, `correctness-gate`, `debug-protocol`,
  `drive`, `perf-optimize`, `latent-audit`.
- **One-way actions need a yes, for that action only:** `agent-release`, `safe-release`,
  `evolve-maintain`, `feature-map`, `issue-handoff`, `verify-loop`.
- **Unattended paths** in `arch-design`, `explain`, `problem-framing`, `issue-handoff`.
- **Safe places to run risky steps:** clean tree or worktree for mutations, scratch copy for breakage,
  `EXPLAIN ANALYZE` on a copy, attacks only on a local or test instance, secrets never pasted.
- **Seams:** `recall` reads `OVERNIGHT.md`, `DRIVE.md` and `BRIEF.md`; `drive` routes to the skills it
  missed; `pick-skill` gains an agent flow; `structure-gate` baseline commands used a path that did
  not resolve.
- `latent-audit`, `senior-review`, `scrutinize`, `project-setup` are report-only unless asked.

## 4.34.0 — 2026-09-27 — the stages of an AI agent, each a skill `drive` can call

- **New `agent-evals`:** the task set and a grader the agent cannot touch, built before the agent and
  proven able to fail.
- **New `agent-prove`:** the agent against a bar set beforehand, over repeated runs, with regression
  checks, a held-out slice and the `threat-model` abuse cases as tasks.
- **New `agent-release`:** kill switch, caps, pinned model and prompt, logged runs, staged rollout, and
  production failures turned into new evals.
- `drive` gains two playbook rows (build an agent; a flaky agent or a changed model), so the chain runs
  from one goal. The other stages reuse existing skills, so there is no separate `agent-build`.

## 4.33.0 — 2026-09-27 — a fix stays inside what it named, and outputs are checked against rules

- **`verify.py scope PATH...`** names the files a fix may touch and freezes what else is on disk.
  A later edit, add or delete outside them fails the run with `OUT OF SCOPE`, and `status` reports
  `out-of-scope`, so the Stop hook blocks over it too. `--add` widens on purpose, `--clear` drops it,
  `--check` lists strays. This is the answer to an agent re-editing code that already worked.
- **Keep-green.** `scope` records every check that passed on the last run. If one goes red, every
  run says `KEEP-GREEN BROKEN` until it is green (`NEWLY RED` says it once).
- **New `compliance.py`** in verify-loop: `schema` (JSON Schema subset, `--strict` closes objects, an
  unsupported keyword is an error not a pass), `privacy` (PII and secret scan, never prints the
  value), `guardrail` (abuse cases against a command), `repeat` (same output every run). Each exits
  0 or 1, so each is a VERIFY.md check.
- `verify-loop` gains "Fixing one thing without disturbing the rest" and "Compliance checks".

## 4.32.0 — 2026-09-27 — verify-loop closes the loop: it remembers, catches edited checks, and stops "done" over red

- **`verify.py` remembers across runs** (`.verify-state.json`, gitignore it). A run now says
  `NEWLY RED` (the last change broke something that passed), `SAME FAILURE x2` (identical output
  twice: re-observe, do not try a third variation) and `BUDGET` (red runs in a row, `--budget`,
  default 5). A `--only` run compares and saves nothing.
- **`verify.py baseline`** freezes the test files and the check commands in VERIFY.md. After that,
  any edit fails the run with `CHECK CHANGED`, even when everything is green: the loop fixes code,
  never the check. A check believed wrong is reported and re-baselined by a person.
- **`verify.py status`** prints one line (`VERIFY-STATE: green | red | stale | never-run | tampered`)
  and exits 0/1/3. Silent in a repo with no VERIFY.md.
- **New hook `verify-stop-gate.py` on `Stop`.** In a repo with a VERIFY.md, after a session that
  edited files, a not-green `status` blocks the stop once (exit 2, reason on stderr) and asks for the
  run and its result. A second stop with the same state always passes. Fails open; `TTE_VERIFY_STOP=0`
  turns it off. This reverses the "no Stop hook" rule from `c479319`: the README and
  `test_hooks.py` now state why this one cannot wedge a session.
- `verify-loop` steps 4-7 rewritten around these signals.

## 4.31.1 — 2026-09-27 — project-setup reaches other agents' instruction files

- `project-setup` now puts the "Project checks" pointer in `GEMINI.md` and `AGENTS.md` too, when the
  project already has them. It never creates either file.

## 4.31.0 — 2026-09-26 — one prompt carries a goal through the skills, and can do it overnight

- **New skill `drive`.** Give it a goal: it matches one playbook (question, bug with unknown or
  known cause, feature, slow, insecure, review, release, or "big/vague"), writes the steps into the
  todo list with the exit check first, and runs each through the skill that owns it. "continue"
  resumes from the list, "new task" drops it and re-matches. Steps an earlier skill already did are
  skipped; a one-way action stops the run.
- **New skill `drive-overnight`.** The same with nobody to ask. Before leaving it fixes the exit
  check, a budget and what is off limits (the one moment it may ask); it works on a branch, logs each
  decision with options and how to undo it in `OVERNIGHT.md`, parks every irreversible action under
  `NEEDS YOU`, stops on a pass or a spent budget, and ends in a VERDICT / DONE / NEEDS YOU / DECIDED /
  FAILED / NEXT report.
- **Routing.** `route-hint.py` sends "while I sleep", "work on it overnight", "run this unattended"
  to `drive-overnight`; "the overnight batch job failed" stays silent. `drive` is invoked by name
  and has no rule (its word is too common for the hook's name-check). `pick-skill` and the README
  list both.
- **Eval `drive-bug-through-skills`.** A bug goal with no known cause: a correct run matches the
  unknown-cause playbook, states the exit check first, diagnoses to `parse.py` before any fix, then
  goes through `evolve-maintain` and `correctness-gate`. Patching the printed total fails the case.
  `drive` now says to invoke each skill with the Skill tool.
- Inspired by the poteto-mode router in Cursor's pstack; here it composes existing skills, adds none
  of their work.

## 4.30.0 — 2026-09-26 — a fresh project can be set up for the skills in one step

- **New skill `project-setup`.** Run once in a new or different codebase: reads the manifest and
  tests to say what kind of system it is, drafts `VERIFY.md` and `FEATURES.md` with the existing
  `verify.py init` / `features.py init` (both refuse to overwrite), and adds a `## Project checks`
  block to the project's `CLAUDE.md` so the next session finds them. It reports what is still a
  draft (`TODO` lines, entry points found) and the skill that finishes each; it never fills them in.
  No new script: it drives the two that exist, and says how to draft by hand where they are absent.
- **Routing.** `route-hint.py` sends "set up this project with these skills", "start fresh here",
  "bootstrap the repo with the skills" to it; "set up the project with Docker" stays silent.
  `pick-skill` and the README list it.
- Tests: route cases and two silence cases in `tests/test_hooks.py`, written red first.

## 4.29.0 — 2026-09-26 — the architecture file is one an agent can build from and check

- **`docs/arch-design.md` is now `key: value` blocks, pinned to a commit.** A header (`at`,
  `question`, `yardstick`, `status`, `verdict`), then one block per finding, decision and move. No
  prose beyond the verdict; the before/after tables and concept map are gone from the file.
- **`scripts/arch-design.py check`.** BROKEN: a missing field, a file or line not in the repo, a
  one-way door with no `confirmed:` or resting on a suspected fact, a strong finding with no number,
  an `after:` naming no move. STALE: a file the moves name changed after `at:` (not once
  `status: landed`). Exit 0 / 1 / 2, summary line `ARCH: ...`.
- **A rerun overwrites its file** (git holds the history); the `-2`, `-3` rule is gone. One-way
  decisions are also appended to the project's decision log, which outlives the moves.
- **Handoffs write no docs.** `arch-design` gets its concept map from `FEATURES.md` or an `explain`
  trace, and asks `code-history` why a thing exists before proposing to delete it. `arch-map` is
  called only when the user wants a picture, and writes its own file, linked from `diagram:`.
- **`explain` gains an overview mode:** the account a senior engineer gives someone joining a
  subsystem (what it is for, the parts and what each must not know, the main path once, what is not
  obvious, where to look next). Saved only when asked, and then pinned to a commit.
- **Routing.** "how does the billing subsystem work" and "onboarding onto X" go to `explain`;
  "how does this function work" stays silent.
- Tests: `tests/test_arch_design.py`, written red first; route cases in `tests/test_hooks.py`.

## 4.28.0 — 2026-09-26 — the agent can find why, teach it, and pick work back up

- **New skill `code-history`.** Answers "why is it this way" from the records, not the code: it
  finds which evidence sources are connected (source control, tracker, docs, chat, error tracking,
  observability, analytics), asks them in parallel, and reports the decision, the reason, whether
  it still holds, and which sources it could not reach. "No recorded reason" is a valid finding.
  `scripts/history.py` reads git for a file, a symbol (`-G`, so an edited value shows up) or a line
  range: commits, bodies, `#123` / `PROJ-45` references, reverts, the introduction. Leaves `WHY.md`.
- **New skill `explain`.** Teaches what a thing is, how it works and why, at the person's pace,
  changing nothing; ends with a prediction the account did not cover, as the check that it landed.
- **New skill `recall`.** Rebuilds recent context from git and the project's notes, reruns the last
  named check, and returns one capsule (goal, done, in flight, open, broken, next, not read).
- **Routing.** `route-hint.py` names the three; "where were we" moved from `evolve-maintain` to
  `recall`, and `explain` stays silent on small questions ("what does this function do?") and on
  failure reports.
- Tests: `tests/test_history.py`, written red first; route cases in `tests/test_hooks.py`.

## 4.27.0 — 2026-09-26 — the app has a way up, and flows have a check

- **`VERIFY.md` gains a `## Run` recipe.** `setup` (seed), `start` (background), `ready` (poll until
  exit 0, within `--timeout`), `stop`, `login`. `verify.py run` brings the app up, runs the checks,
  and always tears it down; a failed setup or an app that is never ready ends the run before any
  check, since those checks would prove nothing. A `run:` check with no recipe gets a note.
- **Journeys.** `## Journey: <name>` with `features:` (two or more, each with its own section) and
  its own checks. Naming a missing feature, or fewer than two, is BROKEN and fails the run. The
  summary line ends `| <j> journeys, <b> broken`; `features.py check` no longer lists journey or
  Run sections as orphans.
- Tests: `RunRecipe` and `Journeys` in `tests/test_verify.py`, `JourneySections` in
  `tests/test_features.py`, written red first.

## 4.26.0 — 2026-09-26 — a change points at the checks it needs

- **`feature-map` gains `impact`.** `features.py impact` takes the changed files (`git diff` against
  HEAD plus untracked, `--base REF`, or `--files a b`) and prints each feature whose entry or trace
  files changed with its VERIFY.md section, so a change reruns only the checks it can affect. Changed
  code that no feature names is listed as a gap.
- **Status can be pinned to a commit** (`proven @ 3f2a1bc: ...`). `check` counts a pin as `drifted`
  when a file of that feature changed since, or the commit does not resolve; `--strict` fails on it.
  A proven claim now expires when the code under it moves.
- Tests: `Impact` and `Drift` in `tests/test_features.py`, written red first (5 failing, then green).

## 4.25.0 — 2026-09-26 — a feature can be followed from click to effect

- **`feature-map` gains `trace:`.** Each feature can carry the path an agent follows, entry point to
  effect: `` `handler` @ file > `callee` @ file > `effect` @ file ``. `check` reports a step missing
  from its file as STALE and a step not referenced from the one before it as BROKEN, so the path
  stays a real call chain, not a remembered one.
- **Summary line and `--strict`** count `broken` and `untraced` features; `init` drafts a `trace:`
  placeholder that does not pass as a trace.
- Same-file hops need a second occurrence only when the symbol has a definition, so an effect such
  as a table name is not mistaken for an uncalled function.

## 4.24.0 — 2026-09-26 — the agent knows what the system has

- **New skill `feature-map`.** `FEATURES.md` records each feature of a web, CLI or desktop app: what
  it does for its user, every way in (route, click target, shortcut, CLI command, menu), the code
  behind it, its `verify-loop` section, and a proven / traced / suspected label saying how it is known.
- **`scripts/features.py`** (stdlib only). `init` drafts the map from entry points found in code
  (server routes, page files, `data-testid` and button ids, accelerators and hotkeys, CLI
  subcommands). `check` reports STALE entry points (the code no longer has them) and what the map
  lacks: unmapped entry points, features with no VERIFY.md link, no label or no description.
  `--strict` fails on those too. Shortcut modifiers are normalised (`Ctrl+O` = `CmdOrCtrl+O`).
- **Proven by hand, kept honest by script:** the skill has the agent run each entry point once to
  earn `proven`; `check` then catches the map drifting when the code moves.
- Router (`tools/route-hint.py`) knows the name; `pick-skill` and the README list it.

## 4.23.0 — 2026-09-26 — the check is built first and lives in the repo

- **New skill `verify-loop`.** For an agent that must tell for itself whether it succeeded: name the
  claim, build the strongest check the environment can run, see it fail once, then loop on its
  failure text until it passes. Five tests for a good check (it can fail, watches the real thing,
  does not come from the work, fails specifically, is cheap to rerun) and a cheating check before
  "done": nothing loosened, skipped or hardcoded.
- **`VERIFY.md` is the feature-to-check map**, kept in the project so the next session runs the same
  checks. One section per feature: its commands, a fail-proof line, and a Blind spots list.
- **`scripts/verify.py`** (stdlib only). `init` drafts VERIFY.md from the test files on disk;
  `run` executes every check and reports what a green run does not cover: unverified features,
  checks never shown able to fail, orphan test files, blind spots. `--strict` fails on those.
- **`PHILOSOPHY.md` habit 3 points at it:** "Past a typo, build the check with `verify-loop`."
- Router (`tools/route-hint.py`) knows the name; no new trigger rule, since "verify" is too common
  a word to route on without misfires. `pick-skill` and the README list it.

## 4.22.0 — 2026-09-26 — a build keeps its state where the next session can find it

- **`build-discipline` rewritten for an agent's loop.** New `BUILD.md`: one line per slice (proof
  line, status, commit) plus a Deferred list whose triggers a machine can check. Resuming reads it
  instead of trusting recollection.
- **The proof line is a command the loop can run**, written before the first edit, ideally a test
  that fails first. A slice gets a budget (about three attempts) and is split rather than ground on.
- **Delegated slices** carry proof line, allowed files and off-limits files; the report is a claim
  until the proof line is rerun.
- Cut the "Common mistakes" and Rules sections, which repeated the steps. "Plan"/"Wire" renamed
  "Aim"/"Connect". 96 → 91 lines.

## 4.21.0 — 2026-09-26 — the habits, written for an agent

- **`PHILOSOPHY.md` reframed from a persona to a loop.** The opening no longer casts the reader as a
  busy senior engineer; it says you are an agent that acts through tools in a loop of observe, act,
  check, and that trust comes from what each step is gated on. Habits 1-7 keep their numbers, names
  and tests (other files cite `#3` and `#7`); the wording now speaks in agent terms: observe before
  any write, tool output is the only fact, an exit condition the loop can run itself, risk tiers on
  actions, re-observe after a second failure.
- **Three agent habits added.** #8 delegate with a standalone brief and verify the subagent's report
  before building on it; #9 put state on disk where the next step can find it; #10 work inside a
  budget and end in a passing check or a stated stop.

## 4.20.0 — 2026-09-19 — architecture is the cost of the next change

- **`arch-design` rewritten around one yardstick: what the next likely change costs.** 36 releases
  had each patched one failure in as a rule plus a matching "common mistake", which took the file
  to 245 lines, the one-way-door rule stated four times, and 20 lines about filenames. It is now one
  loop for both modes (Aim → Measure → Diagnose → Decide → Move), at 173 lines. Every rule that
  carried a test is still there, stated once.
- **Aim names the yardstick first.** Before reading, the run writes down the three changes most
  likely to come next and where they came from. Findings, badges and moves are all judged against
  them.
- **Measure reads the git history, not just the code.** New `scripts/change-map.py` (stdlib only)
  reports spread (modules touched per commit), hidden coupling (file pairs in different modules that
  change together) and churn hotspots. The code shows what's connected; only the history shows what
  changes together. "Change rehearsal" becomes a count instead of a story. Tested in
  `tests/test_change_map.py` against a planted history, with a decoy and a bulk commit.
- **New finding shapes:** shotgun change, hidden coupling, wrong direction, alongside the existing
  ones. The same-reason test, which used to be buried in Shape, is now a named test beside the
  deletion test.
- **Move blocks gain `pays:`**, naming which yardstick change gets cheaper and by how much
  ("add a report field: 6 files → 2"). A move with nothing to pay is tidying, not architecture. After
  the moves land, re-running the rehearsal or the history is the architecture's own proof.
- The file gains a change-cost table (`yardstick change | modules touched now | after the moves`).
  Path rules, `door:`, badges, decision-log reads, and the fallbacks for `arch-map` and
  `latent-audit` are all kept.

## 4.19.0 — 2026-09-18 — a one-way door needs a source, not a memory

- **`arch-design`'s Decide step now enforces the plugin's own ground-truth-over-memory habit on
  one-way doors instead of just labeling confidence after the fact.** A one-way-door recommendation
  (database, public API shape, tenancy model, auth model) used to get a *proven/traced/suspected*
  label bolted on after being written from recall — "Postgres handles our write volume (vendor docs)"
  read as sourced whether or not anyone opened those docs this session. The dependency bar's
  maintenance-health and license checks, and the "say how you know" line, now both require the fetch
  (`WebFetch`/`WebSearch`, the lockfile, a run) to happen *before* the recommendation is written; the
  evidence-labels line at the top says plainly that only *proven* and *traced* can carry a one-way
  door, and *traced* now explicitly covers "opened the source this session," not just "read the code
  chain." The Decide test line and Common mistakes gain the matching checks.

## 4.18.0 — 2026-09-18 — every run gets its own file

- **`arch-design` no longer overwrites a prior run's report.** "The file" used to name the path from
  the topic alone (`docs/arch-design-<topic>.md`), so a second run on the same or a broader area
  landed on the same path and silently rewrote the earlier report. It now lists `docs/` for that
  base name first and, if it's taken, counts up to the next free number (`-2.md`, `-3.md`, …) —
  applied to the bare `docs/arch-design.md` whole-system fallback too. A user-named path still wins
  and still overwrites on rerun, same as before. Common mistakes gains the matching entry.

## 4.17.0 — 2026-09-18 — a finding earns its badge or it's homework

- **`arch-design` gains the deletion test, borrowed from `codebase-design`'s glossary.** Both
  Audit's slop-hunt and Design's complexity bar asked "does this earn its place" without a shared,
  one-line way to answer it. Now both run the same test: undo it in your head — does the complexity
  it hides reappear across callers, or does nothing reappear because there was nothing there to
  hide? Only "reappears" earns a finding, or justifies the layer in the first place.
- **Every audit finding gets a badge — Strong / Worth exploring / Speculative — instead of an
  unscored "how much gets simpler" guess.** The badge *is* the deletion-test result: reappeared with
  a counted cost is Strong, reappeared but the payoff depends on where the code goes next is Worth
  exploring, ambiguous or unmeasured is Speculative. A report where everything comes back
  Speculative is the *clean* verdict wearing a list, and now says so instead of manufacturing a top
  move. The findings table gains a `badge` column; `arch-design-one-owner`'s reference report is
  updated to show the split — the three-copy date format is Strong (counted: three call sites), the
  unused provider interface is Worth exploring (real, but the cost is still zero today).
- **A move can no longer re-litigate a decision the project already settled, unread.** Audit's
  `Map` step now reads the decision log first if one exists, and `Prescribe moves` drops anything
  that only restates a rejected decision — or, if the friction is real enough to reopen it, names
  the entry it contradicts instead of overriding it silently. Design mode's novelty check gets the
  same read-first rule, so both modes check before either writes.
- The one-owner eval's reference report also picks up the `door:` field from 4.16.0's move block,
  which it had missed when that release landed.

## 4.16.0 — 2026-09-18 — a move is a decision wearing work clothes

- **`arch-design`'s audit moves can no longer walk through a one-way door unstopped.** Design mode
  gated deletes, public-shape changes and auth/tenancy merges behind a stop-and-confirm rule; the
  audit-mode move block had no field for it, so a move that quietly did one of those things — drop
  a duplicate store, merge two auth paths — could go straight from "found" to "written" with no
  chance for the user to weigh in. Every move block (audit's and design's) now names a `door:` —
  two-way, land it and go, or one-way, confirmed with the user first — and a move with no answer to
  that question is a question, not a block, same standing as a move with no proof line.
- **`arch-design` gets its first eval coverage for design mode.** The one existing case
  (`arch-design-one-owner`) only ever exercised audit mode's duplicate-hunting; the Decide
  framework — picking the simplest option, naming the cost of a wrong one-way choice, refusing to
  build a seam nobody's paying for — had no case proving it holds. `arch-design-no-new-store` gives
  it one: a CSV-export request where the tempting wrong answers are a plugin interface for a format
  nobody asked for and a brand-new datastore for a few rows of history that the app's one existing
  database already owns. Reference reports pass both a plain-spoken and a differently-worded correct
  answer and fail the report that takes both bait.

## 4.15.0 — 2026-09-17 — one file per question, not one file per skill

- **`arch-design` no longer overwrites its own report.** Every run landed at the same
  `docs/arch-design.md`, so a second design or audit on a different area silently clobbered the
  first. The path is now named after what the run is about — `docs/arch-design-<topic>.md` — and the
  bare filename is reserved for the one run that covers the whole system.
- **Both `arch-design` and `arch-map`'s descriptions drop the implementation detail** (the hardcoded
  filename, "leave it in a file you can open again") that padded them past what a reader scans a
  skill list for. They now match the two-sentence shape every other skill in this plugin uses: what
  it does, then what to use it for.

## 4.14.0 — 2026-09-17 — a router nobody reaches routes nobody

- **`route-hint.py`, a third hook: the skill you needed, named on the prompt that needed it.**
  `pick-skill` had a bootstrapping problem it could not solve from inside a skill file — a router is
  only ever invoked by someone who already suspects a skill applies, and that person usually already
  knows which one. So the routing that matters now happens before anyone chooses anything, on
  `UserPromptSubmit`, whether or not a skill was asked for. `pick-skill` keeps the job a hook
  genuinely cannot do: telling five overlapping skills apart by reading the codebase.
- **The hook routes on what is known, not on the adjective.** "The login is broken" goes to
  `debug-protocol`; "the login is broken because the token expires early" goes to `evolve-maintain`,
  because the diagnosis is already done. That negative check is the one rule `pick-skill` names as a
  trap, and it is now enforced rather than described.
- **Precision over recall, because a hook that fires on ordinary work gets uninstalled** — the same
  reasoning that ruled out a Stop hook in `c479319`. One suggestion per prompt, each skill named at
  most once per session, and silence when the prompt already names a skill, starts with `/`, or is
  ordinary building. `build-discipline` is deliberately absent from the rules: "implement this" is
  the most common thing anyone types. `add error handling to the parser` was routed to
  `debug-protocol` by the first draft and is what tightened the failure pattern — bare `error` no
  longer counts, only a failure being reported.
- **`senior-review` has teeth.** It was the thinnest skill in the repo and the one whose description
  most closely matches how people actually ask ("is this code good?"), which is the worst pairing
  available: the front door asked for the least. Four non-negotiables now sit at the top of the file.
  Question 2 must be *run* — at least two breakages attempted with output pasted, not imagined. Every
  answer carries a file, a command or pasted output, or is reported unanswered rather than left
  blank. The report opens with how much of the project was actually read and what was skipped, which
  is `structure-gate`'s coverage-before-findings rule applied to a review. Praise is a claim too: it
  names a file or the line is cut.
- 13 new tests (77 total, from 64), most of them negative: the ten ordinary prompts that must produce
  no hint at all matter more than the sixteen that must route, because that is the failure that gets
  the hook turned off.

## 4.13.0 — 2026-09-17 — a grader that only accepts its own words is a mirror

- **Every eval case now ships a second correct report, and it has to pass too.** `reference/good.md`
  passing and `reference/bad.md` failing proves a case discriminates; it does not prove *what* it
  discriminates on. A grader quietly tuned to the sentences in `good.md` clears both checks and fails
  every correct report written by anyone else. `reference/good-alt.md` states the same findings in
  another writer's words — different structure, different verbs — and
  `test_alternate_good_reference_passes` asserts it passes. Three cases needed their `expect.json`
  widened before it did, which is the point: they were grading phrasing and nobody could see it.
- **Naming the wrong answer in order to refuse it is no longer counted as making it.** The clearest
  report on a decoy says *do not delete `csv_out.py`* — and substring matching cannot tell that from a
  report recommending the deletion, so the best-written reports tripped the trap hardest. A hit is now
  discounted only when a negation sits in the same clause and within ten words of it. The guard is
  deliberately narrow, because a trap that stops firing costs more than one that fires too often:
  "nothing imports it, **so** delete `csv_out.py`" still trips, the `so` ending the clause that held
  the `nothing`. `NegationGuard` pins both directions with twelve worked examples, including the
  near-miss where the negation belongs to a different clause.
- **The prompts stopped handing over the answer.** Six of them named the finding they existed to
  measure — "find the dead code and check the layers", "the three amounts add up to 42.35", "`SPEC.md`
  is the requirement". An agent that reads the question back scores full marks on those, and the case
  measures nothing the skill added. All six are rewritten as the words someone would really arrive
  with: a customer says the total is short; we are handing this service over next week; it is only a
  couple of small functions, right? `PromptsDoNotLeak` now fails any prompt containing a file a
  planted item requires naming, or a phrase that alone satisfies one.
- **What that test cannot catch is written down next to it.** The leak check works on tokens. The
  semantic kind — "what did someone build that nothing reaches" names no file and gives away the whole
  finding — slips straight through, so `evals/README.md` says a new prompt still has to be read by
  someone asking what it gives away. A guard that oversells its reach is worse than none.

## 4.12.0 — 2026-09-16 — the habit nobody invokes a skill for

- **PHILOSOPHY.md loads itself now.** It is the one file that applies to every task, and until now
  it only reached a session if someone hand-edited `~/.claude/CLAUDE.md` with an `@import` — a step
  the README asked for and nobody performs. A `SessionStart` hook emits it, so installing the plugin
  is the whole install. The README no longer asks.
- **A gate on the habit no skill can catch.** Every skill here is pull: it runs because someone
  asked for it. But the failure they are all written against — code changed, turn ended, "it should
  work" standing in for a result — happens silently, at the moment nobody thinks to invoke anything.
  `tools/unproven-gate.py` reads the transcript and, when source files were edited with nothing run
  since, says so and asks for the label: *proven* (you ran it) / *traced* (you read the whole chain)
  / *suspected* (neither). Reading is not proving: `cat`, `grep`, `ls` and `git status` are inert, so
  a session that only ever read files does not come back green.
- **It runs on `UserPromptSubmit`, not `Stop`, and that is the whole design.** `Stop` is the obvious
  event and this plugin already deleted one Stop hook for cause (c479319 — it linted the suite's own
  verdict lines and could block a session over a malformed one). Reaching the model from `Stop`
  still means `decision: "block"`; the docs now list `additionalContext` there, Anthropic's own
  security-guidance plugin says `Stop` is not in that union and that emitting it corrupts the
  payload (#2159). An unresolved contradiction is a poor thing to bet a hook on, and blocking is the
  wrong answer regardless: a gate that can hold someone in a session they asked to leave gets
  uninstalled, and then it protects nobody. `UserPromptSubmit` takes plain stdout on exit 0, is
  documented on both sides, and fires at the first moment the reminder is actionable.
- **Both hooks fail open, by construction.** Exit 2 on `UserPromptSubmit` blocks the prompt *and
  erases it*; exit 2 on `SessionStart` stops the session starting. Every error path in both scripts
  exits 0 with no output, and the tests assert it for malformed payloads, missing transcripts and
  non-JSON stdin. A reminder is never worth losing someone's typed prompt over.
- **Proved on a real transcript, in both directions.** Truncated to just before this release's test
  run, the gate names `test_hooks.py` and leaves `unproven-gate.py` alone — the latter's selftest had
  already run. With the test run appended, it goes silent. Twenty-four tests cover run-detection,
  source-detection, ordering, dedupe and every fail-open path; `test_no_stop_hook` fails the suite if
  a `Stop` entry ever drifts back into the manifest without the argument that would justify it.

## 4.11.0 — 2026-09-16 — an instruction nobody can check is one you claim for free

- **The skills are tested now.** `evals/` holds six small codebases with a defect already planted,
  the words to hand an agent, and a written statement of what a correct report must say. Three months
  of writing behavioural instructions and nothing checked whether an agent following them finds
  anything. Each case also carries a decoy — a job loaded by name from a config string that is not
  dead, a green suite whose own test asserts the bug, a file that reads as clean because no parser
  could enter it. Missing a finding lowers the score; falling for a decoy fails the case at any
  score, because a confident wrong answer costs the reader more than a miss. `evals/grade.py` is
  stdlib, and every case ships a report that must pass and a report that must fail, so a grader that
  has stopped discriminating fails the repo's own suite instead of sitting green.
- **`*Test:*` came down from PHILOSOPHY.md into the skills.** "Read the whole diff as if reviewing
  someone else's code" costs nothing to claim. Every habit in PHILOSOPHY.md has carried the
  observable that shows it happened; no skill did. Thirty-four of them now sit at the steps that are
  cheapest to fake — the proof line written before the code, the mutation results you can list, the
  plan line quoted rather than described, the inventory built from the source rather than from the
  walk — and a test fails any skill that carries none.
- **`pick-skill`, because five skills answered questions that sound identical from outside.**
  `senior-review`, `scrutinize`, `arch-design` (audit), `structure-gate` and `latent-audit` all
  match "look at my code and tell me what's wrong", and choosing between them meant reading five
  overlapping descriptions at the moment of least context. The disambiguation existed only in the
  README, which is the one file that never enters an agent's context. It is a skill now: one table
  for that fork, one for everything else, and the rule that naming a skill and stopping is the
  router failing.
- **A skill copied out of this repo used to break in two ways, both now closed.** Ten skills asked
  for claims labelled *proven / traced / suspected* and none of them said what the words meant — the
  definition lived only in PHILOSOPHY.md, which no skill referenced. Each now carries the gloss, and
  a test fails any skill that labels evidence without defining the labels. And every handoff that
  the work depends on — `arch-design` to `arch-map` above all, where the file simply never got
  written — now states what to do when that skill isn't loaded, so a pointer degrades into
  instructions instead of a dead end.
- **`arch-design` traded prose for checks.** It ran to 166 lines, much of it re-explaining a file
  format that `arch-map` already owns and stating from both ends a contract that only needs one.
  That is gone; the decision frame, the bars, the stress tests and the move block are untouched. It
  is 186 lines now, not fewer — the twenty are six `*Test:*` lines, the evidence gloss and the two
  fallbacks, which is the trade the whole release is about. The share of the file that changes what
  an agent does went up even though the file got longer.
- The README claimed sixteen skills, the marketplace entry still said fifteen. Both say seventeen,
  and a test now fails if a skill exists that the README never mentions.

## 4.10.0 — 2026-09-15 — the picture is a file, and the audit is one of them

- `arch-map` always leaves a file, and names it. A diagram delivered into the chat is looked at
  once and asked for again the next time someone hits the thing it explains; saving it was an offer
  the user had to accept. Every map now lands at a path named for its view —
  `docs/architecture.md`, `docs/arch-change-<what>.md`, `docs/arch-problems-<what>.md`, so a
  change view never overwrites the map of how things are today — with the path, the headline and
  the top finding as the only three lines in the chat. Markdown by default because GitHub renders
  Mermaid and it diffs as text; the HTML-with-CDN wrapper when the reader wants double-click.
- `arch-design` ends in one file instead of two. The report went to `docs/arch-design.html` and the
  moves to `docs/arch-moves.md` beside it — two documents read together, edited apart, and drifting
  from each other from the first edit. The moves are now the report's last section, under
  `## Moves`, with the evidence for each one a scroll away from the block that builds it.
  `build-discipline` and `issue-handoff` read the same section they always read, in one fewer file.
- The handoff is one move at the end, not a format to follow while working. `arch-design` finishes
  its material — decisions, tables, move blocks — and then hands the lot to `arch-map` with a path;
  it formats nothing itself. The section that says so now sits last, after the work it hands over,
  and says in a line what `arch-map` already owns instead of re-explaining the file.

## 4.9.0 — 2026-09-15 — a skill that names another skill's steps has two jobs

- `evolve-maintain` stops re-teaching four other skills. It carried its own copy of
  `debug-protocol`'s two-direction cause proof, `safe-release`'s expand → backfill → verify →
  contract, `build-discipline`'s build-wire-prove-commit loop, and a common mistake that is
  `latent-audit`'s whole thesis. Four procedures that drift the moment any of them moves, and none
  of them this skill's. It now owns what nothing else does — classify the change, size its reach,
  walk the deprecation ladder, kill the class of bug, keep the log — and names the skill for each
  of the rest.
- The cause rule is a stop, not a note. "Diagnose first" was a sentence inside a bullet; a cause
  nobody proved is the failure this whole skill is arranged around, so it now reads as what it is:
  cause unknown → `debug-protocol`, come back with it proven.
- `perf-optimize` hands the populated-table index to `safe-release` instead of repeating its rule
  in shorter words. "Don't lock the table" is the one-line version of a skill; naming the skill
  gets the batching, the verification and the way back as well.
- `arch-design` names the material it hands `arch-map` rather than listing it again. `arch-map`
  already states what it asks for; stating it from both ends was one contract in two spellings.
- `senior-review` routes the two gaps it could find and had nowhere to send: tangled and worth
  measuring → `structure-gate`, dead weight → `latent-audit`.
- `arch-map` drops the sentence explaining its own example. The removal rule now covers arrows as
  well as boxes, which is what the example was there to show.

## 4.8.0 — 2026-09-15 — the card names what comes out

- `arch-design`'s description now names its deliverables — decisions with options and
  reversibility, a report page when there is more than one module or finding, and the moves written
  out buildable in `docs/arch-moves.md`. It described what the skill thinks about and never what it
  leaves behind, so a reader picking between skills couldn't tell that an audit ends in two files
  on disk. Every other skill's card names its output; this one now does too.
- How a page-delivered report lands is `arch-map`'s, said once. `arch-design` had kept its own copy
  of the rule — land in the file, three lines in the chat, nothing repeated — and a second copy in
  its common mistakes, for four statements of one rule across the two skills. `arch-design` now
  names it as part of what `arch-map` owns and stops restating it.

## 4.7.0 — 2026-09-15 — a handoff is a name, not a retelling

- `arch-design` stops restating what the skills it hands to already say. Its report-page section
  had carried `arch-map`'s whole caller contract — headline, marked boxes and arrows, the tables,
  the path — a second copy of a contract that lives in `arch-map` and drifts the moment either
  moves. It now sizes the report (its own call: chat row for one decision, page for a structure or
  a multi-finding audit), names `arch-map`, and hands over the material.
- The material is named once each. Design mode's **Deliver** and Audit mode's closing line each
  list their own tables; the report-page section no longer lists them again.
- Filing is `issue-handoff`'s, in one line instead of seven. Proving code dead is `latent-audit`'s,
  which has the import graph behind it — `arch-design` reports unreachable code as *suspected* and
  hands it over rather than calling it dead by eye.
- Reversibility stops re-teaching `PHILOSOPHY.md`'s fifth habit and keeps only what is
  architecture's: which doors are one-way.

`arch-design` goes 188 → 166 lines with nothing dropped — every cut line is said once, in the
skill that owns it.

## 4.6.0 — 2026-09-15 — the map draws the page

- `arch-map` owns the report page. It already owned the notation, the legend and the HTML-with-CDN
  file; now it owns building the page too, for the user or for another skill handing it findings:
  what the caller must bring (view, altitude, headline, marked boxes and arrows with their
  `file:line`, the tables, the path), how the file is laid out, and that a report delivered as a
  page lands once — in the file, never also in the chat.
- `arch-design` no longer builds that page itself. It hands `arch-map` the Change view, the path and
  the material — headline, *before* and *after* boxes with evidence, the `!N` / `+` / `−` / `~`
  marks, the tables written out — and keeps the half only it can produce. Anything it can't hand
  over is work still owed, not something the drawing covers for it. The page was described in two
  skills and drawn by the one whose job it isn't; now it's specified once, where it's built.

## 4.5.0 — 2026-09-15 — file it from where it was said

- `issue-handoff` files from the chat as well as from a document. Work is often described in a
  message and never written down, and the skill previously had one rule for that case — don't file
  from the conversation — which left the loose case with nowhere to go. Now the source is *either* a
  document or the chat, and from step 2 the two are filed identically: same five losses, same
  Context block, same reconcile, same held items. Filing from the chat, the user's own words are the
  source block (what you concluded or half-fixed in between is not — it goes to the code to be
  checked first), the split and titles are read back for a yes before anything public is created,
  and each issue number is printed as it lands since there is no document to stamp it into.

## 4.4.0 — 2026-09-15 — the work carries over

- `arch-design` writes its moves to `docs/arch-moves.md` as blocks
  (`cost / files / owner / callers / proof / effort / after`) under one shared **Context**
  paragraph, each held to a self-containment test: someone who never saw the audit must be able to
  build from the block alone. That block is the slice `build-discipline` starts from, so the audit's
  thinking isn't redone by the build.
- New skill **`issue-handoff`**: turns any planned-work document — an audit's moves, a spec, a plan
  — into tracked issues without losing what made it buildable. It runs from the document alone, with
  no memory of the session that wrote it, so it works a week later or from another machine. It
  copies blocks **verbatim** (re-describing work in tidier words is where evidence, proof lines and
  ordering die), prepends the shared Context to every body so standalone issues keep their
  assumptions, checks each item against the five losses (what / why / where / proof / order) and
  **holds back anything it can't complete** rather than filing a placeholder, reconciles against
  existing issues before creating so a re-run can't double the backlog, and stamps each number back
  into the source as it goes.
- `arch-design` no longer files anything and never asks about filing mid-audit: it finishes at the
  file, and `issue-handoff` takes it from there. The moves file holds each move's spec, the tracker
  holds its state — different questions, so neither is a duplicate of the other. A move with no
  nameable proof line is not a move and stays a question in the report.
- `build-discipline` gains **Starting from a brief**: when a design, audit or issue already worked
  the change out, take its proof line and start at Build — after checking the proof line runs from a
  real entry point and the files it names still look the way the brief says.
- `arch-design` audit mode scopes before it maps: the area and the question first, then only what
  those entry points reach. A whole-repo sweep is for a whole-repo question.
- `arch-design` sizes the report to the question: a single decision is answered in the chat as its
  decision row; the HTML page is for multi-module structure or a multi-finding audit.
- `senior-review` ends by naming the one skill to run next on the gap it found.

## 4.3.1 — 2026-09-15 — the report lands once

- `arch-design` was delivering its report twice: once as chat output and once as the HTML file. It
  borrowed `arch-map`'s Change view and inherited that skill's delivery step, which ends in the
  chat. It now borrows the notation only, and the page's contents are specified in one place.

## 4.3.0 — 2026-09-15 — see the change

- `arch-design` writes its report to one HTML file (`docs/arch-design.html` by default): verdict on
  top, *before* and *after* diagrams side by side drawn with `arch-map`'s Change view and legend, then
  the tables. Audit mode's *after* is the map with the moves applied; greenfield draws *after* only.

## 4.2.1 — 2026-09-14 — same picture

- `arch-design` draws its sketch and audit concept map as Mermaid, with audit findings numbered on
  the diagram. Still standalone: it doesn't name another skill. README flow: audit → problems map.

## 4.2.0 — 2026-09-14 — see it

- New skill `arch-map`: draws the codebase as Mermaid traced from real imports and calls, in three
  views (as-is, before → after, problems overlaid), with one legend (`+` added, `−` removed, `~` changed,
  `!N` problem) in color and text, and a `file:line` behind every arrow.

## 4.1.0 — 2026-09-14 — one of each

- `arch-design` gains **One of each**: every concept has one owner everyone calls; merge only what
  changes for the same reason. Stress adds a duplicate count.
- `arch-design` gains **Audit mode** for existing codebases: map the concepts, hunt the slop (same job
  in many places, built for "gonna need", one place doing everything, half-built, noise, no shared
  way), rank by leverage, fix in small proven moves.

## 4.0.0 — 2026-09-14 — philosophy out, skills clean

- The `How to work` section leaves all 13 skills and lives once in `PHILOSOPHY.md` (~560 lines gone).
  Load it via `@<path>/PHILOSOPHY.md` in `~/.claude/CLAUDE.md`.
- `scrutinize` is its own skill again: senior-review's change mode, trimmed.
- `senior-review` is now five plain questions a senior asks of any project (~40 lines, was ~150).
- `perf-optimize` trimmed to the same three modes in ~60 lines.
- `tests/test_philosophy.py` removed; `test_standalone.py` now fails if a skill re-adds the section.

## 3.4.1 — 2026-09-14 — one label set, and a test for the other rules

- `debug-protocol` Rule 4: a failure you can't reproduce is still real. Add the probe that captures
  it next time instead of refusing to debug it.
- Report templates in `correctness-gate`, `evolve-maintain`, `perf-optimize`, `threat-model` and
  `wire-check` accept proven / traced / suspected, the set `How to work` defines. Before, a suspicion
  had no slot and got inflated to "traced".
- Script commands in `latent-audit` and `structure-gate` name the skill's base directory; the
  cwd-relative form failed from a project folder.
- `build-discipline` and `senior-review` drop lines that repeated their own `How to work`.
- `tests/test_standalone.py`: frontmatter names its folder, no skill mentions another, `How to work`
  comes last.

## 3.4.0 — 2026-09-14 — scrutinize, restored in full

- `senior-review` change mode picks up what the 3.0.0 merge of `scrutinize` dropped (from
  thananon/9arm-skills): the report opens with a verdict, ship / fix-then-ship / rework / reject, plus
  the biggest reason; surprises found during the trace get recorded; what the change claims is kept
  apart from what was confirmed; "scrutinize" now triggers the skill.
- Every skill now opens with its own work, and the shared `How to work` section moves to the end.
  Descriptions are single-line, like other plugins' skills.

## 3.3.0 — 2026-09-14 — habits, not tone

- `How to answer` becomes `How to work`: seven engineering habits, each with a test that shows it was
  done. Understand before you change (trace the flow, reproduce, find every caller); ground truth over
  memory; decide what done looks like first; smallest change that holds (every changed line traces to
  the request); size the risk before the move; stop when you're guessing (two failed attempts on one
  idea means re-check the assumption); say how you know, briefly. Scaled to the stakes.
- The old tone rules (answer first, one question, disagree in one line, proven/traced/suspected) are
  folded into habits 1 and 7.
- `build-discipline` drops its "interfaces from ground truth" bullet: habit 2 now covers it.

## 3.2.0 — 2026-09-14 — the philosophy, applied to itself

- `How to answer` gains **Answer first** (every skill's report already opened with its verdict; two didn't)
  and **Say how you know** (proven / traced / suspected, defined once instead of in four skills).
- **Disagree in one line** no longer contradicts the skills that must stop: ask instead when a step
  can't be undone or would fake the result.
- `correctness-gate` and `structure-gate` reports now open with the verdict; `senior-review` ceiling
  mode asks at most one question.
- `structure-report.py` no longer names other skills. Removed `--debt-ledger` / `--require-debt-ledger`:
  the baseline and `repay_at` are the parts that catch regressions; the ledger was prose that drifted,
  and its default path made every `--baseline` run warn projects that never kept one.

## 3.1.0 — 2026-09-14 — the philosophy, back in every skill

- Each skill now opens with a `How to answer` section: the busy-senior-engineer stance from the old
  `PROTOCOL.md` §0, copied into every skill so each still stands alone.
- `tests/test_philosophy.py` fails if the copies drift apart.

## 3.0.0 — 2026-09-14 — independent skills, no governance

- Every skill now stands alone: no `PROTOCOL.md`, verdict lines, evidence-tag law, or hand-offs between skills.
- Removed the `boss` router and the always-on `meta-skills`.
- Merged overlapping skills: `reach-audit` → `wire-check`; `scrutinize` and `toptier-lens` → `senior-review`;
  `symptom-audit` → `perf-optimize`; `ship-gate` and `data-evolution` → new `safe-release`.
- Removed `agents/`, `runs/`, `DECISION_LEDGER.md`, `DEBT_LEDGER.md`, the structure baseline and the CI gates.
- `structure-report.py` and `graph-audit.py` now ship inside `structure-gate/scripts` and `latent-audit/scripts`.

Earlier history (1.x–2.15.0) is in git: `git show 7f1f2d6:CHANGELOG.md`.
