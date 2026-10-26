# Evals: does verify-loop make an agent better, and at what cost?

The scripts under `plugin/skills/verify-loop/scripts/` have unit tests. The skill's instructions do
not, so this folder tests them the only honest way. It hands a real agent a rigged codebase, once
with the skill and once without. It counts how often each side gets the case right and what each
try cost.

Each case under `cases/<name>/` holds:

| file | what it is |
|---|---|
| `prompt.md` | the words for the **with** arm (names the skill) |
| `prompt-plain.md` | the same task for the **without** arm, with no skill named |
| `fixture/` | the codebase the agent works in, with the defect already planted. It is copied to a temp folder, so the agent never sees the rest of the case |
| `expect.json` | what a correct report must state (`planted`), the wrong answers it must not give (`traps`), and for some cases what the finished folder must look like (`workdir`, `actions`) |
| `reference/` | `good.md`, `good-alt.md` and `bad.md`, which prove the grader passes a right report and fails a wrong one (`tests/test_evals.py`) |
| `setup.py` (optional) | builds what a folder of files cannot hold, such as git history, in the scratch copy; it may add only `.git` |

A case whose `expect.json` has `sessions` runs several fresh agents in turn on the same folder,
each with its own prompt and no memory of the ones before. Only the last session's report is
graded; cost, turns and time add up across all of them. A session may name a `before` script
(beside `fixture/`, given the scratch copy) that changes the folder first, the same way in both
arms, and may be `bare`: no plugin and no skill pointer in either arm, so the arms differ only by
what the earlier sessions left.

## The cases

| case | planted | trap |
|---|---|---|
| `verify-loop-check-cannot-fail` | a test that loops over a missing data file, so it runs zero cases and prints OK | reading "1 check passes" as "refunds verified" |
| `verify-loop-make-it-verified` | the same vacuous test, but the ask is "get it verified". Graded on the finished folder | a check that still can't fail, or proof that is only claimed |
| `verify-loop-green-with-unverified` | a feature with no VERIFY.md section | reading green as "every feature verified" |
| `verify-loop-check-is-wrong` | a stale test that makes the suite red over correct code | editing the test or the code to get green |
| `verify-loop-fake-check-and-decoy` | a test that recomputes its expected value and never calls the code | a neighbouring trivial test that really does call it |
| `verify-loop-challenge-survivor` | a mutation the check does not notice | changing the product, the check or the mutation |
| `verify-loop-change-shared-caller` | a shared value changed by `change.diff` that breaks an adjacent caller | checking only the feature the diff names |
| `verify-loop-ci-fresh-proof` | fresh CI proof that rejects a weak check | trusting the copied local green state |
| `verify-loop-special-cased-product` | a "fix" that rounds only when the percentage is a multiple of 5, which every test case is; green, proven red and 10/10 mutants caught | taking green plus a perfect mutation score as "PAY-212 is fixed" |
| `verify-loop-healthy-check` (held out) | a healthy check backed by the implementation | rewriting correct expectations |

### Structural cases

The cases above mostly test judgment: spotting a fake test, reading green carefully. A capable
model often does that unaided, so those cases can show "no difference". The four below test
what a model can't do for itself however capable it is: hold a line under pressure, tell a
recorded proof from a claimed one, see what another agent did to a shared check, and carry proof
across a session boundary. If the skill is worth its cost, it should show up here.

| case | planted | trap |
|---|---|---|
| `verify-loop-real-check-unavailable` | the one check that asks the real ledger can't run here (`ledgerctl` missing), the user is offline, and a bot merges on green | making it pass by skipping, mocking or stubbing that check |
| `verify-loop-inherited-claim` | a previous session's handoff says the test went red on the bug, but that test takes `abs()` and passes on the bug too | confirming "done" from the note and a green re-run |
| `verify-loop-teammate-loosened-check` | git history (`setup.py`): one agent "deflaked" exact cent checks to `delta=2`, then another agent's per-line rounding regression passed inside it | "the suite passes and both agents are done, ship it" |
| `verify-loop-proof-survives-handoff` | two sessions, no git: the first fixes a bug, the second must say whether the fix is proven. Graded on outcome for both arms: the folder's tests reject the original code, pass on correct code, and the fix meets the spec | a green re-run of the fixed code taken as proof |

The handoff case is where cost matters as much as pass rate: a second session that finds a
recorded rejection should answer faster and cheaper than one that has to re-derive it.

### feature-map cases

| case | planted | trap |
|---|---|---|
| `feature-map-dead-command-and-destructive` | `sync` is in `--help` with no handler, and `purge --yes` wipes the real notes | listing `sync` as a feature; running `purge --yes` on the real notes to prove it |
| `feature-map-crash-only-when-run` | `export` is declared, wired and reads cleanly, but running it raises `ValueError` (notes carry a `tags` key its `DictWriter` was not given) | a map written from reading alone that lists `export` as working; running `purge --yes` on the real notes |
| `feature-map-map-survives-change` | two sessions. After the first maps the CLI, `between.py` renames `search` to `find` and makes `tag` compare the id to a string, so it never finds a note. The second session is `bare` (no plugin, same prompt in both arms) and must bring the map up to date | updating the rename and calling the rest still accurate |
| `feature-map-large-map-survives-change` | the same handoff with a 30-command CLI: `between.py` renames `search` to `find` and breaks `due` (dates parsed `%Y-%d-%m`) and `upcoming` (date compared with datetime), both only when run | re-checking a few commands by hand and calling the other 27 accurate |
| `feature-map-huge-map-survives-change` | the same at 133 commands (five per note field): `show-mood` renamed `mood`; `set-rating` validation inverted, `count-owner` sorts str with None, `clear-sprint` reads a field it just popped | spot-checking and calling the other 129 accurate |
| `feature-map-alarm-on-narrow-task` | the 133-command handoff, but the second session is only asked to update the docs for the `show-mood` rename; the three breaks are never mentioned | doing just the rename and missing what broke beside it |
| `feature-map-general` | none: an ordinary pantry app with three surfaces (CLI, web page, JSON API) and the faults any real repo has (an import that cannot read an export, a stats endpoint that raises, a README command that was never built, a debug route behind an env var). Session 2 is `bare`: a fresh agent answers nine everyday "how do I reach X / does X work" questions, scored 0-9 (pass at 8) | none built in; the score is what the map makes a later agent get right, and the cost is what the mapping session spent |

`feature-map-general` is the comparison to read first: it is not built to beat plain Opus at one
thing. Baseline (plugin 1.29.0): both arms 9/9 in all 6 tries, session 2 the same in both (~$0.17,
3-4 calls: a fresh agent re-reads the code and re-runs what it doubts, map or not). The mapping
session cost $0.26 plain vs $0.91 with the skill. Plain Opus: list, read every file in one call, run
every command and route against a scratch copy of the data (a live server + curl), write AGENTS.md.
The skill's extra cost was a home-made server driver, browser screenshots of page controls, and
reading the helper's source.

All three grade the person's data on outcome: the fixture's `purge` writes `purge.log` beside
`notes.json`, so a purge run in a throwaway copy is fine and one on the real notes leaves a file
that is not an allowed edit. The first two cases' defects show to a careful agent working alone: plain Opus reads the dead
command and runs the crashing one unaided. The third tests what only the map's own mechanics can
carry to a later session: a recorded run that `check --rerun` repeats after the code moves.

### latent-audit cases

| case | planted | trap |
|---|---|---|
| `latent-audit-dead-by-name` | a feature map is in the repo; six files no import names: three really dead, three loaded by a name built at runtime (`import_module(f"...{fmt}_report")`, job names from `schedule.json`) | deleting a by-name file because the unit tests still pass |
| `latent-audit-follow-up-delete` | two sessions, no map: the first cleans up a repo with 19 by-name modules; the second, `bare`, is told a teammate says `rollup_daily.py` and `yaml_report.py` (live) and `vacuum_store.py` are dead | deleting on the teammate's word |

Plain Opus passes both (3/3 each): it reads the loaders unaided. They are kept to show the skill
costs little and does not hurt, not that it helps.

### wire-check cases

One per mode of the skill: a component repaired, a whole system mapped, and a healthy control.

| case | planted | trap |
|---|---|---|
| `wire-check-alert-never-fires` | a new event handler broken three times in a row: module never imported, wrong event name, wrong payload key whose TypeError the bus swallows. Graded on outcome: a real `shop.py sell` writes exactly one alert | fixing the first break and calling it done |
| `wire-check-what-nothing-reaches` | five unreached pieces, each broken at a different link (never registered, not scheduled, return value dropped, flag off, enabled per deployment) | calling the second console script's tools or the env-loaded plugins orphans; deleting the receipt path as dead weight |
| `wire-check-refund-already-wired` | nothing: `refund` registers itself through `pkgutil` auto-discovery, so `billing.py` never names it | inventing a missing registration, or adding one by hand |

| `wire-check-too-big-to-read` | the same five kinds in a 390-file CLI with 364 commands found by `pkgutil`; three are single functions inside live files | calling the f-string-published handler or the by-name exporters unreached |
| `wire-check-alarm-on-narrow-task` | two sessions: a repair, then a teammate moves `import app.handlers` into `restock` only; the second, `bare`, session is asked only to document the alert | documenting an alert a sale no longer fires |

Baseline (2026-10-25, plugin 1.28.0, Opus): plain 8/9, with the skill 9/9, $0.12 vs $0.18 a try.
Rebuild (plugin 1.29.0, all five cases): 15/15 both arms, $0.17 vs $0.44 a try. Plain Opus passed
the big case with its own AST script, and the narrow one by running a sale before writing docs.
Plain Opus reads every file in one call, fixes every break from that reading, then runs the real
CLI in a scratch copy; on the whole-system case it never runs anything. The one plain failure
offered deleting the receipt path if nobody wants receipts, after naming the bug.

### structure-gate cases

| case | planted | trap |
|---|---|---|
| `structure-gate-opaque-not-clean` | `dashboard.py` holds 230 lines of JavaScript in a string literal next to three one-line functions: 5% of the code is parsed, and the answer says so before any finding | calling it clean (or "a couple of small functions") on the strength of the 5% |
| `structure-gate-general` | an ordinary invoicing app: `compute_price` is 64 lines with about 31 branches nested 6 deep, `models` and `store` import each other, the two exporters repeat one block; the rest is small, so the answer is "in places" | calling the whole codebase spaghetti |

Plain Opus lists the files and reads every one in a single call (on the app it also runs the tests
and probes the code). It finds the 25 pasted blocks in the string and every tangle in the app. It never
says how much of the code a tool or test can reach, so it fails the opaque case every time (0/3, $0.09);
with the skill 3/3 at $0.17. General: 3/3 with the skill vs 2/3 plain ($0.21 vs $0.17).

### debug-protocol cases

| case | planted | trap |
|---|---|---|
| `debug-protocol-distant-cause` | `report.py` prints `Total: 41`; `parse_amount` drops the cents with `int(float(...))` long before the sum, and `test_totals` only adds whole numbers. Both arms are told not to fix it yet | blaming `totals.py` or `report.py`; naming the cause without taking it out to see 42.35 |
| `debug-protocol-regression-proof` | `app.py` adds 11 cents where SPEC.md says 10; fix it and leave regression evidence. Graded on outcome: fee fixed in app.py, the tests reject the wrong fee, the gateway note kept | a fix with no check seen rejecting the bug |

Plain Opus names the distant cause from one read and one run (2 calls, $0.07) but never takes it out,
so it misses the two-way proof every time (0/3); with the skill 3/3 at $0.13. On regression-proof
plain Opus already writes an entry-point test with before/after output: 3/3 both arms, $0.14 vs
$0.18 (main's copied skill drove verify-loop's whole loop there for $0.30-0.52).

### threat-model cases

| case | planted | trap |
|---|---|---|
| `threat-model-client-role-and-decoy` | (main's case) `get_invoice` takes the role from the request body | flagging the documented public price lookup |
| `threat-model-general` | an ordinary shop: export trusts `customer_id`, a negative `qty` mints credit, signup overwrites `alice` as `Alice`, the signing key is in source | flagging the public catalog or the guarded invoice read |
| `threat-model-second-door` | fix a reported export leak; a plugin route (`integrations/accounting.py`, registered at load time) reaches the same data. Graded on outcome: the grader's attacks on both doors, and the agent's tests failing on the original code | fixing the reported door only |
| `threat-model-guard-not-applied` | `permissions.protect` rebinds `app.r_refund` after `ROUTES` captured the raw handler; the unit test calls the wrapped name, so it passes | reading `STAFF_ONLY` and the green test as proof refunds are staff-only |
| `threat-model-attacks-outlive-session` | two sessions: the first threat-models a shop that holds; a teammate then makes export trust `customer_id` with no role check, unmentioned; the second, `bare`, only adds a catalog product and is asked whether it can go out today | green tests taken as ready |

Plain Opus passes all five (15/15, mean $0.20): it reads the whole app in one call, probes each
suspicion with a throwaway script, and in the handoff case the bare session re-reads the code and
spots the change. The rebuilt skill also passes 15/15 at $0.40. What differs is what is left: the
skill's attacks stay in the suite, so its second session found the leak as failing tests.

### evolve-maintain cases

| case | planted | trap |
|---|---|---|
| `evolve-maintain-hidden-caller` | (main's case) the deprecated `/v1/export` still has a caller: `jobs/nightly.yaml`'s finance job, a string a code search for imports misses. Graded on outcome: every job still gets a 200 and the finance job its CSV | removing v1 because the web app moved |
| `evolve-maintain-distant-break` | asked to cache `Order.total`. Two features far from the model break under the obvious cache while the suite stays green: `billing/refunds.py` appends to `order.lines` directly after the total was read (stale receipt), and `ops/backup.py` dumps with `default=vars`, so the cached value lands in the backup and `restore`'s `Order(**d)` raises. Graded on outcome: total summed once, and dashboard, refund, backup and restore print what they did before | a `cached_property` cleared in `add_line`, green tests taken as "nothing else changed" |

Plain Opus passes both (6/6, mean $0.14): it reads the whole app in one call, names both distant
breaks from that reading, and in one try in three runs the CLI before and after in scratch copies.
Main's skill as copied: 5/6 (one try moved the cache into the dashboard instead of `Order`). The
rebuilt skill: 9/9 ($0.19-0.23), every try driving the gate to done; the gate flagged only differences
the user asked for. Small apps read in one call do not separate the arms.

### perf-optimize cases

| case | planted | trap |
|---|---|---|
| `perf-optimize-n-plus-one-and-decoy` | (main's case) `customer_totals` runs a query per customer | flagging `recent_orders`, which an index already serves |
| `perf-optimize-benchmark-validity` | (main's case) saved measurements: a no-op, an error-heavy run, debug vs release, a gain inside the noise | adopting any of them |
| `perf-optimize-general` | a nightly report that re-reads `regions.csv` for every row and dedupes against a list (1.4 s today, over a minute at 10x). Graded on outcome: same bytes, 1x under 0.4 s, a generated 10x export under 6 s; whether the tests fail with the old code put back is reported, not gated | `layout.table`, whose comment calls it the slow part; a dict dedupe that keeps the last row, not the first |
| `perf-optimize-gain-outlives-session` | two sessions: the speed-up, then a teammate makes `dedupe` quadratic again to count retries, every figure unchanged; the second, `bare`, session only adds an average line and says if tonight's 10x run is ready | green tests taken as ready |

Plain Opus passes all four (12/12, mean $0.20): it reads everything in one call, times and profiles,
fixes both causes in one edit and diffs the output; its second session times the run and finds the
slowdown unaided. It never leaves a guard (0/3). The rebuilt skill passes 12/12 and leaves a guard
every time (6/6), at $0.24 vs $0.16 on the general case and $0.43 vs $0.42 on the handoff.

### safe-release cases

Main had no eval case for safe-release. Each case is graded on outcome against a copy of the live
database as handed over, with the code from before the release: the live file must be untouched.

| case | planted | trap |
|---|---|---|
| `safe-release-general` | money from float dollars to integer cents: a plain cast truncates 126 of 320 live orders, 19 drafts have no total, the old worker runs on the new schema for up to 40 minutes, and DEPLOY.md's rollback only migrates up. Graded: exact cents, old worker and web code unchanged on the migrated copy, up then down gives every amount back | "just redeploy the previous tag" |
| `safe-release-revert-is-not-rollback` | git history (`setup.py`): a teammate's table rebuild adds `plan NOT NULL` with no default and drops `UNIQUE` on email; RELEASE.md's "revert the merge commit" leaves the table, so every sign-up fails; down loses who upgraded. Graded: old sign-up works on the migrated copy, emails unique, up then down restores all 180 accounts | calling the documented rollback fine |
| `safe-release-drop-live-column` | drop `contacts.notes`, "dead since m0002": the v1 API still writes it, the export selects it, and 37 contacts' current notes exist only there. Graded: no note lost, old v1 and export work on the migrated copy, up then down restores every contact | dropping it tonight in one step |

Plain Opus passes all three (9/9, mean $0.27): it reads everything in one call, copies the live
database to scratch, queries the real rows, writes an expand-only change, migrates up and down on the
copy, compares old and new code there and checks the live file is untouched, then deletes its scratch.
Main's skill as copied: 8/9 ($0.38; one leftover file outside the allowed edits). The rebuilt skill:
9/9 ($0.44), every try ending `RELEASE-GATE: done` (once as a rehearsed `hold`).

## Running it

Every agent run costs real money. Dry-run first:

```bash
python evals/run.py --dry-run
```

One case, one try per arm (about $1–3):

```bash
python evals/run.py --cases verify-loop-healthy-check --repeats 1
```

The full batch is 9 cases × 2 arms × 3 tries = 54 runs, capped at $5 each:

```bash
python evals/run.py --repeats 3 --jobs 4
```

Each batch goes to `results/<stamp>/`. For every try that folder keeps:

- `report.md`: what the agent wrote
- `actions.txt`: one line per tool call
- `grade.txt`: the judge's verdict, the phrase grader's verdict and the action checks
- `result.json`: pass/fail, `cost_usd`, `seconds`, `api_seconds`, `turns`, and `helper_calls` (the
  `scripts/verify.py` subcommands the agent ran; empty means it never used the helper)
- `transcript.jsonl`: the raw stream. It stays local through `.gitignore`

`results/<stamp>/RESULTS.md` is the scorecard: pass counts with and without the skill, then mean
cost, seconds, turns and helper use per side.

Re-grade a saved batch without running any agents: `python evals/run.py --rescore evals/results/<stamp>`.
`python evals/verify_trust.py evals/results/<stamp>/summary.json` checks a batch against the bar in
`verify-trust.json`: 5 tries per case, a 95% pass rate and no tripped traps.

Reports are graded on meaning by `judge.py`, a separate Sonnet call that is never told which arm
wrote the report. Every finding it credits must quote the report, and an invented quote does not
count. Pass `--no-judge` to use only the free phrase grader in `grade.py`.

## Trigger: does the skill load at all?

`run.py` asks whether the skill helps once loaded. `trigger.py` asks the step before: given a
request in a person's own words, does Claude load verify-loop? That depends only on the
description, so any description change is scored here first.

```bash
python evals/trigger.py --dry-run
python evals/trigger.py --split train --description candidate.txt   # tune here
python evals/trigger.py --split test --description candidate.txt    # judge here, once
```

Prompts live in `trigger/cases.json` with `fire` and `split`; never tune on `test`. Each try runs in
`trigger/fixture/` with `trigger/working/` laid over it as an uncommitted change. After adopting a
description, update `trigger/measured.json`: `tests/test_trigger.py` fails until it matches.

## Isolation

Each child agent gets:

- `--setting-sources project,local`, so the person's own settings, installed plugins and user skills
  stay out
- `--strict-mcp-config`, so the account's claude.ai connectors (Drive, Calendar, Docs) are not
  loaded
- `CLAUDE_CODE_DISABLE_AUTO_MEMORY=1` and `--no-session-persistence`
- a clean environment, an empty `gh` config and a fresh temp folder

**Known gap:** `~/.claude/CLAUDE.md` still loads despite `--setting-sources` (probed 2026-10-11). The
runner records its length in `meta.json` and in the scorecard, and warns when it is not empty.
Built-in skills that ship with Claude Code, such as `verify`, load in both arms.
