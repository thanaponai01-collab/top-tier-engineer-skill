# Helper commands

Commands beyond the core loop (`init`, `run`, `baseline`, `status`, `tests`, `scope`). None of them
proves anything on its own: a scaffold is a draft, and only `run --strict` then `status` decides done.

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
suggested `fail-signal:` with the real behavioral one, then prove rejection as in step 4.

## Parallel checks: --jobs

`run --jobs N` runs up to N checks at once and prints results in recipe order, so output, loop
memory and verdict match a serial run. Use it only when no two checks share an app, port, database
or written file; the default of 1 is the safe choice for `## Run` recipes that drive one live app.
A check that fails only under `--jobs` is sharing something: run it serially and fix the coupling.

## Flaky checks: --stress and --quarantine

`run --stress N` runs each check N times. A check that both passes and fails is reported flaky and
added to the `quarantined` list in `.verify-state.json`. `run --quarantine` then keeps those checks'
failures from failing a **non-strict** run; strict runs ignore quarantine.

Quarantine is a diagnostic aid, not a way to get green. Only checks that `--stress` found flaky
belong there; never add one by hand or edit the list. Report each quarantined check as a gap and
fix its cause (seed, ordering, port, timing) before claiming done.
