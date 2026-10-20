# Multi-agent swarms

Use `verify.py swarm` when two or more agents (`VERIFY_AGENT=<name>`) share a repository or worktree
pool and want to divide verification work without stepping on each other or deadlocking on
`require: independent`.

## Work-stealing queue

```bash
# Inspect every feature's next verification step and active leases
python <skill-base>/scripts/verify.py swarm . [--json]

# Atomically claim the next eligible feature for this agent
VERIFY_AGENT=alpha python <skill-base>/scripts/verify.py swarm . --claim [--role any|worker|judge] [--lease 600] [--json]

# Release a claim early (or all claims held by this agent)
VERIFY_AGENT=alpha python <skill-base>/scripts/verify.py swarm . --release [Feature]
```

`swarm` classifies each feature in `VERIFY.md` into its next required step:

`map` -> `fix` -> `prove` -> `freeze` -> `challenge` -> `independent` -> `run` -> `done`

- **Evidence advances the queue, not `--done`.** A lease is bound to `(feature, action)`. As soon as
   the real receipt (`challenge` / `run`), `baseline`, or strict pass lands in `.verify-state.json`,
   the feature's `action` advances automatically and the old lease drops. Calling `--done Feature`
   releases the lease; if the evidence is not there yet, the feature stays open on the same step.
- **Role and independence routing.** `--role judge` claims only `independent`, `challenge`, `prove`
  or `freeze` items. An `independent` or `judge` item is **never** handed to an agent listed in
  `frozen_by` for that feature, so a judge agent automatically picks up checks frozen by other
  agents.
- **Exit codes (`--claim`).** `0` claimed an item (or all features are `done`), `3` waiting (all
  open items are leased by other agents or need a different `VERIFY_AGENT` for independence), `2`
  usage or missing `VERIFY.md`.

## Two-agent peer swarms (`verified_by`)

With `require: independent`, a check frozen by `alpha` must pass `--strict` under a different
`VERIFY_AGENT`. When `beta` runs `verify.py run --strict` and a check frozen by `alpha` passes on
the current check signature and tree signature, `verify.py` records `verified_by[check]` in the
shared state (`.verify-state.json`).

That means two peer agents can verify a multi-feature repo without needing a third "final runner"
agent:

1. `alpha` proves and freezes Feature A; `beta` proves and freezes Feature B.
2. `beta` runs `--strict` (verifying Feature A); `alpha` runs `--strict` (verifying Feature B).
3. Either agent's full `run --strict && status` is now green on that unchanged `(signature, tree)`
   because every check has an independent `verified_by` record. Any edit to the tree or check
   invalidates `verified_by`.

## Zero-file inline challenges

In a multi-agent checkout, writing a `mutation.json` file into the working tree dirties `git status`
and invalidates concurrent tree signatures. Pass the mutation inline on the command line instead:

```bash
VERIFY_AGENT=alpha python <skill-base>/scripts/verify.py challenge . \
  --feature Auth --file auth.py \
  --before "return tok == 'secret'" --after "return tok != 'secret'"
```

The working tree stays untouched: `challenge` copies the tree once into a scratch directory, checks
the original, applies the mutation in place, runs only the target feature's checks (unless a
`## Run` recipe is active), and records the receipt in `.verify-state.json`.

## Repo-wide mutation survey (`swarm --auto`)

```bash
python <skill-base>/scripts/verify.py swarm . --auto [--diff [REF]] [--jobs N] [--max 15] [--json]
```

Surveys every mapped feature with checks and a `fail-signal:` in one pass, sharing the scratch lane
pool across features and reporting both per-feature and repo-wide mutation scores (`caught`,
`survived`, `uncovered`). Like `challenge --auto`, this is a read-only diagnostic survey and never
writes receipts to `.verify-state.json`.
