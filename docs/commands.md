<!-- context-id: commands:plugin -->
<!-- context-type: command -->
# Command index

Run from the plugin repository root with Python on PATH. Setup helpers use --repo for the target
project and live in the installed plugin; target projects need not copy them.

| Purpose | Command | Source / execution status |
|---|---|---|
| Repository tests | python -m unittest discover tests | CLAUDE.md; pass count changes, run it |
| Skill catalog | python tools/catalog.py --check | tools/catalog.py; run on this refresh |
| Plugin validation | claude plugin validate ./plugin | Claude CLI; also validate . for the marketplace |
| Foundation inventory | python plugin/skills/project-foundation/scripts/foundation.py --repo . inventory | foundation.py; read-only scoped discovery |
| Foundation structure | python plugin/skills/project-foundation/scripts/foundation.py --repo . check | foundation.py; structural only |
| Remember selected inputs | python plugin/skills/project-foundation/scripts/foundation.py --repo . remember --sources plugin/scripts/verify-stop-gate.py | foundation.py; writes ignored cache only |
| Retrieve context | python plugin/skills/project-context/scripts/context.py --repo . search architecture --limit 5 | context.py; read-only |
| Maintain index | python plugin/skills/project-context/scripts/context.py --repo . index --files docs/architecture.md docs/commands.md | context.py; writes ignored index |
| Live evaluation | python evals/run.py --cases project-setup-full-foundation --repeats 1 --jobs 1 | evals/run.py; consumes account usage |

These helper definitions do not establish product verification. Read actual --help when exact
usage matters. CI, pushes, deployment and external mutations are outside ordinary setup.
