<!-- context-id: architecture:plugin -->
<!-- context-type: architecture -->
<!-- context-paths: hooks/hooks.json, tools/front-door.py, tools/start-here-hook.py, skills/project-context/scripts/context.py, skills/project-setup/SKILL.md -->
# Plugin architecture

Independent skills do engineering work; shared project memory makes their results discoverable.
This is the observed implementation, not a proposed product architecture.

```mermaid
flowchart LR
  hooks["hooks/hooks.json"] --> entry["tools/front-door.py"]
  entry --> catalog["CATALOG.md"]
  entry --> summary["tools/start-here-hook.py"]
  summary --> records["Project Markdown records"]
  drive["skills/drive"] --> records
  setup["skills/project-setup"] --> instructions["agent routing instructions"]
  drive --> executor["agents/drive-executor.md: bounded implementation"]
  drive --> worker["agents/setup-reader.md: bounded read-only discovery"]
  context["skills/project-context/scripts/context.py"] --> records
  context --> index[".project-context/index.sqlite: disposable FTS cache"]
  update["skills/project-update"] --> records
```

## Boundaries and sources
| Relationship | Source |
|---|---|
| SessionStart invokes front-door | hooks/hooks.json:4 |
| Front-door reads generated catalog | tools/front-door.py:46 |
| Front-door loads compact project summary | tools/front-door.py:57 |
| Summary reads current intent/work pointers | tools/start-here-hook.py:104 |
| Drive owns foundation preparation/routing | skills/drive/references/model-routing.md:1 |
| Economy worker is declarative read-only configuration | agents/setup-reader.md:1 |
| Context indexes authoritative files transactionally | skills/project-context/scripts/context.py:161 |
| Context retrieves indexed or fallback records | skills/project-context/scripts/context.py:201 |
| Update maintains only affected records | skills/project-update/SKILL.md:20 |

## Invariants and limits
- Files own facts; SQLite is a rebuildable ignored cache. RUN.json owns driven execution state.
- Worker findings are inputs; the coordinator checks sources and product evidence before claims.
- Diagram arrows to workers/records describe instructed behavior; actual agent compliance needs evals.
- Representative context-paths identify boundary changes; internal edits need no automatic redraw.
- Mermaid source inspected; renderer not run. One live setup-only trial passed; tier delegation remains unvalidated.
