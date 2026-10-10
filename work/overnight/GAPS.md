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

### G0. The evals measured the installed plugin, not the repo's [proven] (fixed tonight)
Every eval agent inherited the person's user settings: `enabledPlugins` (with
top-tier-engineer@4.58.1 from the marketplace cache) and `~/.claude/CLAUDE.md` (which imports
PHILOSOPHY.md). The "without" arm was never plain. In the first batch tonight it opened
`agent-design` and `arch-map` itself. Both arms also got PHILOSOPHY.md, whose "work directly for small changes" is a standing nudge
not to open a skill. (The with arm's staged copy overrides the installed one of the same name, a
host fact traced on 2026-10-10, so it was not listing two copies.) That affects every with/without
row in RESULTS.md and the routing numbers (route_live uses the same runner). Fixed with `--setting-sources project,local` in `agent.build_command`, plus a
regression test. **Re-measured: routing is 21 of 34 isolated, against 11 of 34 under the leak**
[proven: ROUTING.md, $2.51]. Which of the two leaks drove the jump is *suspected* (likely PHILOSOPHY's "work directly",
as suspected on 2026-10-10). All 13 remaining misses open *no* skill, never a wrong one: debug-protocol
(2), problem-framing, arch-design, correctness-gate, perf-optimize, senior-review, latent-audit,
code-history, explain, verify-loop, agent-trace, evolve-maintain. The route-hint hook stays at 13/34
and points the wrong way on 6 rows, three of them toward manual-only skills (recall, onboard-system,
drive-overnight) that the model can't open.

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

### G7. code-history finds the reason but never leaves it for the next session [proven: 0 of 2 runs]
Both clean and contaminated plugin-arm runs traced INC-212 and the batching commit correctly and wrote
no `WHY.md`, though step 6 says to when the answer took digging. This is exactly the
context a fresh session needs ("why is this 60?"), and it evaporates with the chat. The
trigger ("real digging") is a judgement call the agent always resolves as "no". **Fix:** make it
unconditional when the trail had more than one record, or when the answer is *expired*.

### G8. scrutinize says "scratch checkout" but gives no way to make one [proven: 1 run]
The plugin-arm agent switched the person's own checkout between branches to run the code, and left
it on `main` rather than the branch it was handed. The plain arm read the diff and never switched.
The skill's "Run things… from a scratch checkout" has no command behind it. **Fix:** name it:
`git worktree add <tmp> <branch>` (remove afterwards), and never `checkout` in the person's tree.

### G9. Files written outside the repo the person named [proven: 3 runs]
In a folder containing the repo, agents wrote deliverables beside it: arch-map's plain arm
(`docs/architecture.md`), issue-handoff's plugin arm (`issue-bodies.md`), agent-design's plain arm.
A fresh session opening the repo never sees them. Mostly a case-wording issue (fixed by naming the
repo root), but the skills that save context (arch-map, issue-handoff, feature-map, code-history)
never say "inside the repository root you were given". **Fix:** one line in each skill that saves
context.

## Evals: the 17 new cases, isolated (claude-sonnet-5-5)

| case | without | with | reading |
|---|---|---|---|
| `agent-design-tool-contract` | 1/1 | 1/1 | no difference: Sonnet 5.5 already does this unaided |
| `agent-drift-refusals-under-a-steady-rate` | 1/1 | 1/1 | no difference: Sonnet 5.5 already does this unaided |
| `agent-evals-grader-cannot-fail` | 1/1 | 1/1 | no difference: Sonnet 5.5 already does this unaided |
| `agent-prove-average-hides-safety` | 1/1 | 1/1 | no difference: Sonnet 5.5 already does this unaided |
| `agent-release-launch-readiness` | 0/2 | 1/1 | **helps**: plain missed the unredacted logs and the all-at-once rollout (both tries) |
| `agent-trace-first-divergence` | 1/1 | 1/1 | no difference: Sonnet 5.5 already does this unaided |
| `arch-map-readme-is-not-the-code` | 0/2 | 1/1 | **helps**: plain drew a good map but cited no `file:line` per arrow (both tries) |
| `code-history-expired-reason` | 1/1 | 1/1 | no difference: Sonnet 5.5 already does this unaided |
| `evolve-maintain-hidden-caller` | 1/1 | 1/1 | no difference: Sonnet 5.5 already does this unaided |
| `explain-config-beats-readme` | 1/1 | 1/1 | no difference: Sonnet 5.5 already does this unaided |
| `feature-map-dead-command-and-destructive` | 1/1 | 1/1 | no difference: Sonnet 5.5 already does this unaided |
| `issue-handoff-no-tracker` | 0/2 | 1/1 | **helps**: plain would file M3 with no proof line (both tries) |
| `onboard-system-stale-architecture` | 0/1 | 0/1 | no measured difference: both refresh the stale doc; the judge flips on the invariant item |
| `pick-skill-slow-is-a-bug` | 0/2 | 1/1 | **helps**: routed to debug-protocol, measured before editing; plain edited first (both tries) |
| `problem-framing-unattended-brief` | 0/2 | 1/1 | **helps**: plain wrote a brief with no outcome-shaped job, no measurable criteria and no failure states (both tries) |
| `recall-stale-proof` | 1/1 | 1/1 | no difference: Sonnet 5.5 already does this unaided |
| `scrutinize-unchanged-caller` | 1/1 | 1/2 | **hurts once**: 1 of 2 runs switched the person's checkout and left it on `main` (G8) |

Total spend on the clean batch and reruns: $3.42. One or two tries per arm: a direction, not a rate.

**What this says about the skills.** Where the skill helps, it's the same pattern: a **checklist the
plain agent half-remembers** (agent-release's five controls, problem-framing's measurable criteria
and failure states, issue-handoff's "no proof line, don't file", arch-map's evidence per arrow) or
**an order of operations** (pick-skill: measure, then edit). Where the plain agent already wins, the
case hinges on spotting one planted defect in a small repo, and Sonnet 5.5 does that unaided. Those
10 cases still guard against regressions, but they don't show value. Making them discriminate
needs scale (a decoy buried in a bigger repo) or persistence checks (G7: did the next session get
the answer?), not cleverer decoys.

## What to do, in order

| # | move | gap | cost | proof it worked |
|---|---|---|---|---|
| 1 | Front door prints RUN.json status (active/blocked, next stage, unresolved actions) | G1 | ~20 lines in start-here-hook + a test | hook test with an active RUN.json fixture |
| 2 | Triggers ("Use for…") in the 5 bare descriptions, starting with code-history and build-discipline | G4 | 5 frontmatter lines + `catalog.py --write` | `route_live.py`: code-history and verify-loop rows turn right |
| 3 | code-history: WHY.md entry unconditional when the trail had >1 record or the reason expired | G7 | 2 lines | `code-history-expired-reason` with a gated WHY.md check, 3 tries |
| 4 | plan-work and agent-design link their file from the work doc (`include:`) | G2 | 1 line each | a recall case whose NEXT lives in PLAN.md |
| 5 | scrutinize names the scratch checkout (`git worktree add`, never `checkout` in place) | G8 | 1 line | `scrutinize-unchanged-caller` 3 tries, read_only holds |
| 6 | Move the 31× memory paragraph to PHILOSOPHY.md/front door; one evidence-label definition | G5 | mechanical, 31 files | catalog check + suite |
| 7 | One context role table (role → file → owner → when to read) used by recall and the front door | G6 | design change | recall case over a repo with every role present |
| 8 | Harder or longer variants of the 10 no-difference cases (scale, persistence) | evals | a case each | plain arm fails ≥2 of 3 |

Each skill change re-runs its case with `--repeats 3` (CLAUDE.md), now isolated.
