# Helper commands

Commands beyond the core loop (`init`, `run`, `baseline`, `status`, `tests`, `scope`). None of them
proves anything on its own: a scaffold is a draft, and only `run --strict` then `status` decides done.

## advance: automatic mechanical progression

```bash
python <skill-base>/scripts/verify.py advance . --json
```

Runs a fresh whole check pass when inputs have changed or no run exists, freezes the baseline
once every feature has proof and needs only freezing/running, then runs the whole recipe strictly.
It reuses the existing feature state machine, receipts and gates. It never executes `NEXT` text,
edits product/check/recipe files, invents mutations, overrides a refused baseline, or impersonates
a judge. Checks run with the same authority and side effects as `run`.

`--max-steps 3` bounds automatic actions, `--timeout 120` bounds each check and `--jobs 1` controls
check concurrency. These are action/per-check limits, not a total wall-time or monetary budget.
Use parallel checks only when their resources are isolated. Each automatic run bypasses the result
cache. Unchanged completed or decision-bound work runs no checks; use `--refresh` after environment,
package, service or other external inputs change. File signatures cannot observe those changes.

The single JSON object contains `stop`, `orientation` (see below), `steps` (action, exit, input fingerprint and output: the
last two lines of a passing action, the final 16 KB of a failing one), `tasks` (feature, action,
detail, paths and next instruction), `report` (the canonical caller answer) and `exit`. Plain output
prints the last 20 lines of each failing action and ends with the `ANSWER DRAFT`, so an agent needs
no `--json` and no second command to see why a step failed. The last executed batch is also retained as `last_advance`
in this agent's existing state. No state schema migration or second task queue is required.

Plain output opens with `ORIENT` lines, read from the state as it was before any step ran: the
recorded verdict and the frozen files (`; the recorded proof holds, no re-run needed` when it is
green and current), one line per feature with its `path:` files and whether it has a fail-proof
receipt for the current checks, and `changed since baseline:` with every file whose content differs
from when `baseline` last ran. A session that inherits the repo reads these instead of opening files.
`orientation` in `--json` holds the same: `state`, `detail`, `frozen`, `features` (`name`, `paths`,
`receipt`) and `changed_since_baseline` (`null` before the first baseline that records it).

| Stop | Meaning | Exit |
|---|---|---|
| `done` | Current strict green, including existing gates | 0 |
| `needs-agent` | Mapping, repair, proof, challenge, independent judgment or unresolved strict gate | 3 |
| `waiting` | Another agent holds a feature lease, or another advance executor holds its lock | 3 |
| `stale` | Inputs/state changed while planning, or product/check files changed while executing | 3 |
| `budget` | Automatic action limit reached; resume with another invocation | 3 |
| `blocked` | Environment failure; report where the check can run | 1 |
| `guard` | Changed frozen checks, scope/state violation or refused baseline | 1 |
| `invalid` | Missing/empty recipe, invalid limits or execution setup error | 2 |

A returned task is an instruction for the caller, not authorization to spawn or message agents.
After resolving it, invoke `advance` again. It stops on a current strict failure rather than
rerunning unchanged gates. Independent verification always yields a task for a genuinely separate
context; `advance` never assigns itself another identity.

Automatic baseline/run operations affect the whole recipe, so a foreign active feature lease
blocks both. A separate `.verify-state.advance.lock` serializes advance invocations for this
checkout/state directory. It is never stolen by age: after a crashed process, confirm it has exited
before removing that lock. Input fingerprints detect changes before dispatch and file changes
after execution; they do not isolate arbitrary concurrent editors or other CLI commands. Use an
isolated checkout when other processes may edit the same product/checks during execution.

## loop: rerun and triage, no edits

```bash
python <skill-base>/scripts/verify.py loop . --scope app.py --max 5 [--strict]
```

Pins `--scope`, then runs the recipe and prints `triage` on each red. It **never edits code**:
every iteration reruns the same tree, so an unchanged red stops at `SAME FAILURE x2` on the second
pass. Use it when something else changes files between passes (another process, a person). An agent
fixes in its own turns with `verify.py run` after each slice. Without `--strict`, a pass here is
`partial`, not done.

## watch: rerun on file changes

```bash
python <skill-base>/scripts/verify.py watch . --max-runs 1
```

Polls the tree and runs `run --affected` (non-strict) on each change. With the default
`--max-runs 0` it never exits; an agent's shell blocks until its timeout. Always pass `--max-runs`
from an agent, or run it in the background.

## triage

Classifies the last red run as harness-gap, spec-drift or product-gap with a suggested action
(`--json` for callers). It reads the output text, so treat it as a first guess and confirm against
[triage](triage.md) before editing anything.

## contract: breaking-change diff

```bash
python <skill-base>/scripts/verify.py contract old.json new.json [--json]
```

Compares two OpenAPI or JSON Schema files. Red (exit 1) for a removed path, a removed HTTP method,
a newly required field or a removed property; exit 2 when a file is missing or unparsable (YAML
needs PyYAML installed). It checks the documents only, not the running service, and misses type
changes, enum narrowing and response-shape changes. Keep the old spec as a committed `oracle:`.

## Scaffolds

| Command | Writes | Still needed before it counts |
|---|---|---|
| `scaffold-driver [--type web\|api\|cli]` | `scripts/smoke_driver.py`, `.verify-evidence/` | Real actions and assertions on concrete values |
| `scaffold-ui --route /path` | `scripts/smoke_ui.py` | Assertions on page content, not just a load |
| `scaffold-oracle spec.json [--type openapi\|schema]` | `scripts/smoke_api.py` or `scripts/validate_schema.py` | Expected bodies; the API probe only checks a successful status |

Each prints a suggested VERIFY.md section; it does not edit VERIFY.md. Paste it, replace the
suggested `fail-signal:` with the real behavioral one, then prove rejection (the `prove` step in SKILL.md).

## Parallel checks: --jobs

`run --jobs N` runs up to N checks at once and prints results in recipe order, so output, loop
memory and verdict match a serial run. Use it only when no two checks share an app, port, database
or written file; the default of 1 is the safe choice for `## Run` recipes that drive one live app.
A check that fails only under `--jobs` is sharing something: run it serially and fix the coupling.

Every check gets two environment variables so it can stop sharing:

- `VERIFY_SLOT`: `0`..`N-1`. No two checks running at the same time share a slot (serial runs: `0`).
  Key scratch folders, database names or temp files on it: `tmp/run-$VERIFY_SLOT/`, `test_db_$VERIFY_SLOT`.
- `VERIFY_PORT`: a TCP port that was free when the check started, fresh for each check. A check that
  starts its own app binds it there and probes it there:

```python
port = int(os.environ.get("VERIFY_PORT", "8000"))  # default keeps the check runnable by hand
app = start_app(port=port)
assert get(f"http://127.0.0.1:{port}/health").status == 200, "expected 200 from /health"
```

The OS picked the port, so another process can still take it before the app binds; a check that
sees "address already in use" should be rerun, not loosened. The `## Run` app is one shared
instance: its checks do not use these variables, and `--jobs` stays 1 for them.

## Selecting checks: --affected and --record-coverage

`run --affected [REF]` runs only features whose commands, oracles, `paths:` or test files match a
file changed since REF. File names miss imports: with coverage.py importable, `run --record-coverage`
records the repo files each check's Python processes execute (in `.git/verify-loop/coverage.json`,
shared by worktrees), and `--affected` also selects a feature when a changed file is in that set.
Non-Python checks record `measured: false` and keep the name match. Re-record after large changes.
Without coverage.py the built-in stdlib profiler (`sys.setprofile`) still records every executed Python repo file out of the box.

A selection can still miss something (a data file, a new import), so `--affected` never makes
`--strict` green: a strict affected run exits 1 with `SELECTED`. Prove done with a whole run.

## Fast inner loop and the shared result cache

A non-strict `run` and `watch` fingerprint the tree from a stat cache: a file whose size, mtime and
(on POSIX) ctime are unchanged since it was last hashed is not read again, as git's index works. An
edit that restores all three goes unseen until a full pass. `run --strict`, `status`, `ci` and
`challenge` always read every byte, and both ways give the same signature for honest stat data,
so `status` can still judge a run the fast way recorded. Files changed in the last 2 seconds are
always re-read.

`run` then reuses a pass that any agent or worktree already proved for the same command on the
same content (the key is the command plus the tree signature). The output says
`[CACHED: proved <time> by <agent>]` and `CACHED  n check(s) reused`; `--json` sets `cached` per
result and in the summary. The rules:

- Only passes are kept, and only from runs whose tree did not move while they ran.
- A pass recorded by a non-strict (stat-trusting) run never satisfies `--strict`; strict reuses
  only passes recorded under a full, every-byte signature.
- No caching with a `## Run` recipe (checks depend on a live app) or with `--stress`.
- The cache lives in Git's common directory (`.git/verify-loop/`), shared by every worktree, or in
  `.verify-state-cache/` outside Git; with a state directory (below), under that directory.

The signature covers files in the tree, not the machine: installed packages (`node_modules`,
virtualenvs, `vendor`), environment variables, the clock and the network are outside it. After
changing any of those, or for a check that depends on them, run with `--no-cache`.

## assess: one read-only call

```bash
python <skill-base>/scripts/verify.py assess . [--max 8] [--timeout 120] [--jobs 1]
```

First the `ORIENT` lines (see `advance`) for what the repo itself recorded, so a handoff learns
what the last session left even though assess keeps its own state elsewhere. Then a fresh whole run
(recording which files each check executes), then `challenge --auto` on every
feature whose checks all passed: its `path:` files, or with no `path:` the non-test files its
checks imported (up to three), at most `--max` mutations each. Then `report` and its
`ANSWER DRAFT`. Every survived or uncovered mutation becomes `GAP survived a wrong result`, which
`answer-check` asks the answer to name. State goes to the `--assess` folder unless `--state-dir` is
given; the printed `Then:` line carries the same option.

## Assess without touching the repo: --assess, --state-dir, VERIFY_STATE_DIR

By default `run`, `challenge`, `baseline`, `scope`, `swarm` and the rest write `.verify-state*.json`
and a lock into the repo, and caches into `.git/verify-loop/`. Every subcommand takes `--assess` or
`--state-dir DIR` (or reads `VERIFY_STATE_DIR`) to put all of it in `<dir>/<repo name>-<path hash>/`
instead, one folder per repo; `--assess` uses `VERIFY_STATE_DIR` if set, else `verify-loop-assess`
in the system temp directory, and also sets `PYTHONDONTWRITEBYTECODE=1` and
`PYTEST_ADDOPTS=-p no:cacheprovider` so Python checks leave no bytecode or pytest cache behind. Pass
the same option to every command of one assessment: `report --assess` reads what `run --assess`
saved, and `report` without it reads the repo's own state. `NEXT` and `review` reproduce lines carry
`--state-dir` so follow-ups land in the same place. Scratch copies made by `challenge`, `swarm --auto`
and `ci` keep their state inside themselves. What stays out of reach: files the checks themselves
write, and the `scaffold-*` commands, whose job is to add files to the project.

## Many agents in one checkout: VERIFY_AGENT

Saves are atomic and locked, and concurrent saves merge, so agents sharing a checkout do not
corrupt or revert each other's state. Without a name they still share one loop memory: one
agent's run becomes the other's NEWLY RED and `status`. Give each agent its own with
`VERIFY_AGENT=<name>` (letters, digits, `-`, `_`): its last run, rounds, scope and `status` live in
`.verify-state.<name>.json`. The baseline, re-baselines and rejection receipts stay shared in
`.verify-state.json`, so a new name neither escapes a freeze nor has to re-prove a check. Agents
still share the files on disk: a green `status` is true of the tree as it is now, edits by others
included. Give agents that edit the same files separate worktrees. Gitignore `.verify-state*`.

## Flaky checks: --stress and --quarantine

`run --stress N` runs each check N times. A check that both passes and fails is reported flaky and
added to the `quarantined` list in `.verify-state.json`. `run --quarantine` then keeps those checks'
failures from failing a **non-strict** run; strict runs ignore quarantine.

Quarantine is a diagnostic aid, not a way to get green. Only checks that `--stress` found flaky
belong there; never add one by hand or edit the list. Report each quarantined check as a gap and
fix its cause (seed, ordering, port, timing) before claiming done.
