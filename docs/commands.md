<!-- context-id: commands:plugin -->
<!-- context-type: command -->
# Command index

Run from the plugin repository root with Python on PATH. Setup helpers use --repo for the target
project and live in the installed plugin; target projects need not copy them.

| Purpose | Command | Source / execution status |
|---|---|---|
| Repository tests | python -m unittest discover tests | CLAUDE.md; 452 tests passed on this refresh |
| Skill catalog | python tools/catalog.py --check | tools/catalog.py; run on this refresh |
| Plugin validation | claude plugin validate . | Claude CLI; passed with root CLAUDE.md loading warning |
| Foundation inventory | python skills/drive/scripts/foundation.py --repo . inventory | foundation.py; read-only scoped discovery |
| Foundation structure | python skills/drive/scripts/foundation.py --repo . check | foundation.py; structural only |
| Remember selected inputs | python skills/drive/scripts/foundation.py --repo . remember --sources tools/front-door.py | foundation.py; writes ignored cache only |
| Retrieve context | python skills/project-context/scripts/context.py --repo . search architecture --limit 5 | context.py; read-only |
| Maintain index | python skills/project-context/scripts/context.py --repo . index --files docs/architecture.md docs/commands.md | context.py; writes ignored index |
| Live evaluation | python evals/run.py --cases project-setup-full-foundation --repeats 1 --jobs 1 | evals/run.py; consumes account usage |

These helper definitions do not establish product verification. Read actual --help when exact
usage matters. CI, pushes, deployment and external mutations are outside ordinary setup.
