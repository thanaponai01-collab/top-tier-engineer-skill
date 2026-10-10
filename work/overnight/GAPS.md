# Skill gaps: fresh-session context (2026-10-11)

What a fresh agent session gets from this plugin, measured. Labels: **proven** = ran it,
**traced** = read the whole chain, **suspected** = neither. Ranked by what they cost a fresh session.

## What a fresh session loads today [proven: measured]

| layer | size | source |
|---|---|---|
| SessionStart front door | ~3.1 KB | CATALOG card + start-here summary (`tools/front-door.py`) |
| PHILOSOPHY.md | 5.6 KB | only via the user's global CLAUDE.md import, not the plugin |
| Project CLAUDE.md | 2.1 KB | repo |
| Skill listing (35 descriptions) | 5.6 K chars | host listing |
| One skill when loaded | 2–10 KB (median ~5 KB) | SKILL.md |

About 4k tokens before any work: lean. The problems are in what is *missing*, not in size.

## Gaps

### G1. SessionStart never mentions an active driven run [traced]
`RUN.json` is declared authoritative for execution state (drive, recall, pick-skill). But the
SessionStart path (`front-door.py` → `start-here-hook.compact_summary`) reads only the intent and
work documents and the decisions excerpt. It never reads `RUN.json`. A fresh session in a repo with an
active or blocked run is not told: the run exists, its next stage, and above all **unresolved
external actions** (journaled "unknown", which must be reconciled, never replayed). Only `/recall`
(manual-only) or the Stop gate surface it, and the Stop gate fires at the end of the session.
Observed tonight: this repo's own active RUN.json was invisible in the front-door output.
**Fix:** one line from `run.py status` in the front door when RUN.json exists:
`Driven run: active | next: <stage> | unresolved actions: <n> (reconcile first)`.

### G2. Plans and agent contracts are invisible to resume [traced]
`plan-work` writes `PLAN.md`; `agent-design` writes `docs/agent-design.md`. Neither `recall`'s read
list nor the start-here pointer keys (`intent:`, `work:`) include them, and nothing tells
plan-work to link PLAN.md from the work document. A session resuming a planned, parallel build
reads BUILD.md and misses which slices can run together and each slice's check.
**Fix:** plan-work links `PLAN.md` from the work document (`include: PLAN.md (slices, order,
checks)`), which recall already follows. Same for agent-design → `docs/agent-design.md`.

### G3. Double-encoded UTF-8 in three skills [proven: byte scan]
`build-discipline` (10 places, including the core "Aim → Build → Connect → Prove → Commit" and
"Exists → Registered → Routed → Invoked → Reachable" ladders), `code-history` (3), `feature-map` (2) contain
`â†’` (for →) and `Â·` (for ·) sequences, bytes `c3 a2 e2 80 a0 e2 80 99` and `c3 82 c2 b7`. An agent reads "Aim â†’ Build". It's cosmetic for a person, but it is the
first line of the skill's core procedure.

### G4. Five descriptions say what, not when [proven: frontmatter scan]
`build-discipline`, `code-history`, `feature-map`, `project-context`, `project-update` have no
"Use for/when…" trigger. The other 30 do. Routing is the plugin's measured weakest point: in
ROUTING.md the agent opened the right skill 11 of 34 times, and in most misses it opened no skill
at all. code-history's request ("Why does the scheduler load digest by name… who decided?") was
missed. Descriptions are the only routing signal the host gives the model.

### G5. The memory boilerplate is in 31 skills [proven: paragraph scan]
The same 259-character "Project memory: retrieve missing facts with `project-context`…" paragraph
ends 31 SKILL.md files, and PHILOSOPHY.md says it again. CLAUDE.md's own rule is "the shared
philosophy lives once; skills hold only their own work." It costs ~65 tokens per loaded skill, and
it doesn't scale: every new skill copies it, and a wording change is a 31-file edit. The
evidence-label line is likewise repeated 24 times in three variants, and onboard-system defines
*traced* differently ("followed code" vs "read the whole chain").

### G6. Skills tell the agent to save context but nothing indexes where [traced]
Context files a skill may write: BRIEF.md (+archive, brief/<area>), BUILD.md (+archive,
work/<area>), RUN.json, OVERNIGHT.md, DRIVE.md, PLAN.md, VERIFY.md, FEATURES.md (+features/),
WHY.md (+archive), docs/architecture.md, docs/arch-design.md, docs/agent-design.md,
docs/arch-change-*.md, .project-context/. recall's gather step lists 13 sources by hand, and each
new skill adds another. The start-here block has keys for only two roles (`intent`, `work`). This
works at 35 skills but doesn't scale cleanly. **Fix direction:** one role table (role → file →
owner skill → when to read) in project-setup's handoff reference, read by recall and the front door,
instead of each skill naming files.

(Behavioural gaps from the live evals: see "Evals" below, filled in when the runs finish.)
