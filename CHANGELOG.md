# Changelog

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
