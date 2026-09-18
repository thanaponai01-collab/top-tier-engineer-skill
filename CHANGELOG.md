# Changelog

## 4.19.0 — 2026-09-18 — a one-way door needs a source, not a memory

- **`arch-design`'s Decide step now enforces the plugin's own ground-truth-over-memory habit on
  one-way doors instead of just labeling confidence after the fact.** A one-way-door recommendation
  (database, public API shape, tenancy model, auth model) used to get a *proven/traced/suspected*
  label bolted on after being written from recall — "Postgres handles our write volume (vendor docs)"
  read as sourced whether or not anyone opened those docs this session. The dependency bar's
  maintenance-health and license checks, and the "say how you know" line, now both require the fetch
  (`WebFetch`/`WebSearch`, the lockfile, a run) to happen *before* the recommendation is written; the
  evidence-labels line at the top says plainly that only *proven* and *traced* can carry a one-way
  door, and *traced* now explicitly covers "opened the source this session," not just "read the code
  chain." The Decide test line and Common mistakes gain the matching checks.

## 4.18.0 — 2026-09-18 — every run gets its own file

- **`arch-design` no longer overwrites a prior run's report.** "The file" used to name the path from
  the topic alone (`docs/arch-design-<topic>.md`), so a second run on the same or a broader area
  landed on the same path and silently rewrote the earlier report. It now lists `docs/` for that
  base name first and, if it's taken, counts up to the next free number (`-2.md`, `-3.md`, …) —
  applied to the bare `docs/arch-design.md` whole-system fallback too. A user-named path still wins
  and still overwrites on rerun, same as before. Common mistakes gains the matching entry.

## 4.17.0 — 2026-09-18 — a finding earns its badge or it's homework

- **`arch-design` gains the deletion test, borrowed from `codebase-design`'s glossary.** Both
  Audit's slop-hunt and Design's complexity bar asked "does this earn its place" without a shared,
  one-line way to answer it. Now both run the same test: undo it in your head — does the complexity
  it hides reappear across callers, or does nothing reappear because there was nothing there to
  hide? Only "reappears" earns a finding, or justifies the layer in the first place.
- **Every audit finding gets a badge — Strong / Worth exploring / Speculative — instead of an
  unscored "how much gets simpler" guess.** The badge *is* the deletion-test result: reappeared with
  a counted cost is Strong, reappeared but the payoff depends on where the code goes next is Worth
  exploring, ambiguous or unmeasured is Speculative. A report where everything comes back
  Speculative is the *clean* verdict wearing a list, and now says so instead of manufacturing a top
  move. The findings table gains a `badge` column; `arch-design-one-owner`'s reference report is
  updated to show the split — the three-copy date format is Strong (counted: three call sites), the
  unused provider interface is Worth exploring (real, but the cost is still zero today).
- **A move can no longer re-litigate a decision the project already settled, unread.** Audit's
  `Map` step now reads the decision log first if one exists, and `Prescribe moves` drops anything
  that only restates a rejected decision — or, if the friction is real enough to reopen it, names
  the entry it contradicts instead of overriding it silently. Design mode's novelty check gets the
  same read-first rule, so both modes check before either writes.
- The one-owner eval's reference report also picks up the `door:` field from 4.16.0's move block,
  which it had missed when that release landed.

## 4.16.0 — 2026-09-18 — a move is a decision wearing work clothes

- **`arch-design`'s audit moves can no longer walk through a one-way door unstopped.** Design mode
  gated deletes, public-shape changes and auth/tenancy merges behind a stop-and-confirm rule; the
  audit-mode move block had no field for it, so a move that quietly did one of those things — drop
  a duplicate store, merge two auth paths — could go straight from "found" to "written" with no
  chance for the user to weigh in. Every move block (audit's and design's) now names a `door:` —
  two-way, land it and go, or one-way, confirmed with the user first — and a move with no answer to
  that question is a question, not a block, same standing as a move with no proof line.
- **`arch-design` gets its first eval coverage for design mode.** The one existing case
  (`arch-design-one-owner`) only ever exercised audit mode's duplicate-hunting; the Decide
  framework — picking the simplest option, naming the cost of a wrong one-way choice, refusing to
  build a seam nobody's paying for — had no case proving it holds. `arch-design-no-new-store` gives
  it one: a CSV-export request where the tempting wrong answers are a plugin interface for a format
  nobody asked for and a brand-new datastore for a few rows of history that the app's one existing
  database already owns. Reference reports pass both a plain-spoken and a differently-worded correct
  answer and fail the report that takes both bait.

## 4.15.0 — 2026-09-17 — one file per question, not one file per skill

- **`arch-design` no longer overwrites its own report.** Every run landed at the same
  `docs/arch-design.md`, so a second design or audit on a different area silently clobbered the
  first. The path is now named after what the run is about — `docs/arch-design-<topic>.md` — and the
  bare filename is reserved for the one run that covers the whole system.
- **Both `arch-design` and `arch-map`'s descriptions drop the implementation detail** (the hardcoded
  filename, "leave it in a file you can open again") that padded them past what a reader scans a
  skill list for. They now match the two-sentence shape every other skill in this plugin uses: what
  it does, then what to use it for.

## 4.14.0 — 2026-09-17 — a router nobody reaches routes nobody

- **`route-hint.py`, a third hook: the skill you needed, named on the prompt that needed it.**
  `pick-skill` had a bootstrapping problem it could not solve from inside a skill file — a router is
  only ever invoked by someone who already suspects a skill applies, and that person usually already
  knows which one. So the routing that matters now happens before anyone chooses anything, on
  `UserPromptSubmit`, whether or not a skill was asked for. `pick-skill` keeps the job a hook
  genuinely cannot do: telling five overlapping skills apart by reading the codebase.
- **The hook routes on what is known, not on the adjective.** "The login is broken" goes to
  `debug-protocol`; "the login is broken because the token expires early" goes to `evolve-maintain`,
  because the diagnosis is already done. That negative check is the one rule `pick-skill` names as a
  trap, and it is now enforced rather than described.
- **Precision over recall, because a hook that fires on ordinary work gets uninstalled** — the same
  reasoning that ruled out a Stop hook in `c479319`. One suggestion per prompt, each skill named at
  most once per session, and silence when the prompt already names a skill, starts with `/`, or is
  ordinary building. `build-discipline` is deliberately absent from the rules: "implement this" is
  the most common thing anyone types. `add error handling to the parser` was routed to
  `debug-protocol` by the first draft and is what tightened the failure pattern — bare `error` no
  longer counts, only a failure being reported.
- **`senior-review` has teeth.** It was the thinnest skill in the repo and the one whose description
  most closely matches how people actually ask ("is this code good?"), which is the worst pairing
  available: the front door asked for the least. Four non-negotiables now sit at the top of the file.
  Question 2 must be *run* — at least two breakages attempted with output pasted, not imagined. Every
  answer carries a file, a command or pasted output, or is reported unanswered rather than left
  blank. The report opens with how much of the project was actually read and what was skipped, which
  is `structure-gate`'s coverage-before-findings rule applied to a review. Praise is a claim too: it
  names a file or the line is cut.
- 13 new tests (77 total, from 64), most of them negative: the ten ordinary prompts that must produce
  no hint at all matter more than the sixteen that must route, because that is the failure that gets
  the hook turned off.

## 4.13.0 — 2026-09-17 — a grader that only accepts its own words is a mirror

- **Every eval case now ships a second correct report, and it has to pass too.** `reference/good.md`
  passing and `reference/bad.md` failing proves a case discriminates; it does not prove *what* it
  discriminates on. A grader quietly tuned to the sentences in `good.md` clears both checks and fails
  every correct report written by anyone else. `reference/good-alt.md` states the same findings in
  another writer's words — different structure, different verbs — and
  `test_alternate_good_reference_passes` asserts it passes. Three cases needed their `expect.json`
  widened before it did, which is the point: they were grading phrasing and nobody could see it.
- **Naming the wrong answer in order to refuse it is no longer counted as making it.** The clearest
  report on a decoy says *do not delete `csv_out.py`* — and substring matching cannot tell that from a
  report recommending the deletion, so the best-written reports tripped the trap hardest. A hit is now
  discounted only when a negation sits in the same clause and within ten words of it. The guard is
  deliberately narrow, because a trap that stops firing costs more than one that fires too often:
  "nothing imports it, **so** delete `csv_out.py`" still trips, the `so` ending the clause that held
  the `nothing`. `NegationGuard` pins both directions with twelve worked examples, including the
  near-miss where the negation belongs to a different clause.
- **The prompts stopped handing over the answer.** Six of them named the finding they existed to
  measure — "find the dead code and check the layers", "the three amounts add up to 42.35", "`SPEC.md`
  is the requirement". An agent that reads the question back scores full marks on those, and the case
  measures nothing the skill added. All six are rewritten as the words someone would really arrive
  with: a customer says the total is short; we are handing this service over next week; it is only a
  couple of small functions, right? `PromptsDoNotLeak` now fails any prompt containing a file a
  planted item requires naming, or a phrase that alone satisfies one.
- **What that test cannot catch is written down next to it.** The leak check works on tokens. The
  semantic kind — "what did someone build that nothing reaches" names no file and gives away the whole
  finding — slips straight through, so `evals/README.md` says a new prompt still has to be read by
  someone asking what it gives away. A guard that oversells its reach is worse than none.

## 4.12.0 — 2026-09-16 — the habit nobody invokes a skill for

- **PHILOSOPHY.md loads itself now.** It is the one file that applies to every task, and until now
  it only reached a session if someone hand-edited `~/.claude/CLAUDE.md` with an `@import` — a step
  the README asked for and nobody performs. A `SessionStart` hook emits it, so installing the plugin
  is the whole install. The README no longer asks.
- **A gate on the habit no skill can catch.** Every skill here is pull: it runs because someone
  asked for it. But the failure they are all written against — code changed, turn ended, "it should
  work" standing in for a result — happens silently, at the moment nobody thinks to invoke anything.
  `tools/unproven-gate.py` reads the transcript and, when source files were edited with nothing run
  since, says so and asks for the label: *proven* (you ran it) / *traced* (you read the whole chain)
  / *suspected* (neither). Reading is not proving: `cat`, `grep`, `ls` and `git status` are inert, so
  a session that only ever read files does not come back green.
- **It runs on `UserPromptSubmit`, not `Stop`, and that is the whole design.** `Stop` is the obvious
  event and this plugin already deleted one Stop hook for cause (c479319 — it linted the suite's own
  verdict lines and could block a session over a malformed one). Reaching the model from `Stop`
  still means `decision: "block"`; the docs now list `additionalContext` there, Anthropic's own
  security-guidance plugin says `Stop` is not in that union and that emitting it corrupts the
  payload (#2159). An unresolved contradiction is a poor thing to bet a hook on, and blocking is the
  wrong answer regardless: a gate that can hold someone in a session they asked to leave gets
  uninstalled, and then it protects nobody. `UserPromptSubmit` takes plain stdout on exit 0, is
  documented on both sides, and fires at the first moment the reminder is actionable.
- **Both hooks fail open, by construction.** Exit 2 on `UserPromptSubmit` blocks the prompt *and
  erases it*; exit 2 on `SessionStart` stops the session starting. Every error path in both scripts
  exits 0 with no output, and the tests assert it for malformed payloads, missing transcripts and
  non-JSON stdin. A reminder is never worth losing someone's typed prompt over.
- **Proved on a real transcript, in both directions.** Truncated to just before this release's test
  run, the gate names `test_hooks.py` and leaves `unproven-gate.py` alone — the latter's selftest had
  already run. With the test run appended, it goes silent. Twenty-four tests cover run-detection,
  source-detection, ordering, dedupe and every fail-open path; `test_no_stop_hook` fails the suite if
  a `Stop` entry ever drifts back into the manifest without the argument that would justify it.

## 4.11.0 — 2026-09-16 — an instruction nobody can check is one you claim for free

- **The skills are tested now.** `evals/` holds six small codebases with a defect already planted,
  the words to hand an agent, and a written statement of what a correct report must say. Three months
  of writing behavioural instructions and nothing checked whether an agent following them finds
  anything. Each case also carries a decoy — a job loaded by name from a config string that is not
  dead, a green suite whose own test asserts the bug, a file that reads as clean because no parser
  could enter it. Missing a finding lowers the score; falling for a decoy fails the case at any
  score, because a confident wrong answer costs the reader more than a miss. `evals/grade.py` is
  stdlib, and every case ships a report that must pass and a report that must fail, so a grader that
  has stopped discriminating fails the repo's own suite instead of sitting green.
- **`*Test:*` came down from PHILOSOPHY.md into the skills.** "Read the whole diff as if reviewing
  someone else's code" costs nothing to claim. Every habit in PHILOSOPHY.md has carried the
  observable that shows it happened; no skill did. Thirty-four of them now sit at the steps that are
  cheapest to fake — the proof line written before the code, the mutation results you can list, the
  plan line quoted rather than described, the inventory built from the source rather than from the
  walk — and a test fails any skill that carries none.
- **`pick-skill`, because five skills answered questions that sound identical from outside.**
  `senior-review`, `scrutinize`, `arch-design` (audit), `structure-gate` and `latent-audit` all
  match "look at my code and tell me what's wrong", and choosing between them meant reading five
  overlapping descriptions at the moment of least context. The disambiguation existed only in the
  README, which is the one file that never enters an agent's context. It is a skill now: one table
  for that fork, one for everything else, and the rule that naming a skill and stopping is the
  router failing.
- **A skill copied out of this repo used to break in two ways, both now closed.** Ten skills asked
  for claims labelled *proven / traced / suspected* and none of them said what the words meant — the
  definition lived only in PHILOSOPHY.md, which no skill referenced. Each now carries the gloss, and
  a test fails any skill that labels evidence without defining the labels. And every handoff that
  the work depends on — `arch-design` to `arch-map` above all, where the file simply never got
  written — now states what to do when that skill isn't loaded, so a pointer degrades into
  instructions instead of a dead end.
- **`arch-design` traded prose for checks.** It ran to 166 lines, much of it re-explaining a file
  format that `arch-map` already owns and stating from both ends a contract that only needs one.
  That is gone; the decision frame, the bars, the stress tests and the move block are untouched. It
  is 186 lines now, not fewer — the twenty are six `*Test:*` lines, the evidence gloss and the two
  fallbacks, which is the trade the whole release is about. The share of the file that changes what
  an agent does went up even though the file got longer.
- The README claimed sixteen skills, the marketplace entry still said fifteen. Both say seventeen,
  and a test now fails if a skill exists that the README never mentions.

## 4.10.0 — 2026-09-15 — the picture is a file, and the audit is one of them

- `arch-map` always leaves a file, and names it. A diagram delivered into the chat is looked at
  once and asked for again the next time someone hits the thing it explains; saving it was an offer
  the user had to accept. Every map now lands at a path named for its view —
  `docs/architecture.md`, `docs/arch-change-<what>.md`, `docs/arch-problems-<what>.md`, so a
  change view never overwrites the map of how things are today — with the path, the headline and
  the top finding as the only three lines in the chat. Markdown by default because GitHub renders
  Mermaid and it diffs as text; the HTML-with-CDN wrapper when the reader wants double-click.
- `arch-design` ends in one file instead of two. The report went to `docs/arch-design.html` and the
  moves to `docs/arch-moves.md` beside it — two documents read together, edited apart, and drifting
  from each other from the first edit. The moves are now the report's last section, under
  `## Moves`, with the evidence for each one a scroll away from the block that builds it.
  `build-discipline` and `issue-handoff` read the same section they always read, in one fewer file.
- The handoff is one move at the end, not a format to follow while working. `arch-design` finishes
  its material — decisions, tables, move blocks — and then hands the lot to `arch-map` with a path;
  it formats nothing itself. The section that says so now sits last, after the work it hands over,
  and says in a line what `arch-map` already owns instead of re-explaining the file.

## 4.9.0 — 2026-09-15 — a skill that names another skill's steps has two jobs

- `evolve-maintain` stops re-teaching four other skills. It carried its own copy of
  `debug-protocol`'s two-direction cause proof, `safe-release`'s expand → backfill → verify →
  contract, `build-discipline`'s build-wire-prove-commit loop, and a common mistake that is
  `latent-audit`'s whole thesis. Four procedures that drift the moment any of them moves, and none
  of them this skill's. It now owns what nothing else does — classify the change, size its reach,
  walk the deprecation ladder, kill the class of bug, keep the log — and names the skill for each
  of the rest.
- The cause rule is a stop, not a note. "Diagnose first" was a sentence inside a bullet; a cause
  nobody proved is the failure this whole skill is arranged around, so it now reads as what it is:
  cause unknown → `debug-protocol`, come back with it proven.
- `perf-optimize` hands the populated-table index to `safe-release` instead of repeating its rule
  in shorter words. "Don't lock the table" is the one-line version of a skill; naming the skill
  gets the batching, the verification and the way back as well.
- `arch-design` names the material it hands `arch-map` rather than listing it again. `arch-map`
  already states what it asks for; stating it from both ends was one contract in two spellings.
- `senior-review` routes the two gaps it could find and had nowhere to send: tangled and worth
  measuring → `structure-gate`, dead weight → `latent-audit`.
- `arch-map` drops the sentence explaining its own example. The removal rule now covers arrows as
  well as boxes, which is what the example was there to show.

## 4.8.0 — 2026-09-15 — the card names what comes out

- `arch-design`'s description now names its deliverables — decisions with options and
  reversibility, a report page when there is more than one module or finding, and the moves written
  out buildable in `docs/arch-moves.md`. It described what the skill thinks about and never what it
  leaves behind, so a reader picking between skills couldn't tell that an audit ends in two files
  on disk. Every other skill's card names its output; this one now does too.
- How a page-delivered report lands is `arch-map`'s, said once. `arch-design` had kept its own copy
  of the rule — land in the file, three lines in the chat, nothing repeated — and a second copy in
  its common mistakes, for four statements of one rule across the two skills. `arch-design` now
  names it as part of what `arch-map` owns and stops restating it.

## 4.7.0 — 2026-09-15 — a handoff is a name, not a retelling

- `arch-design` stops restating what the skills it hands to already say. Its report-page section
  had carried `arch-map`'s whole caller contract — headline, marked boxes and arrows, the tables,
  the path — a second copy of a contract that lives in `arch-map` and drifts the moment either
  moves. It now sizes the report (its own call: chat row for one decision, page for a structure or
  a multi-finding audit), names `arch-map`, and hands over the material.
- The material is named once each. Design mode's **Deliver** and Audit mode's closing line each
  list their own tables; the report-page section no longer lists them again.
- Filing is `issue-handoff`'s, in one line instead of seven. Proving code dead is `latent-audit`'s,
  which has the import graph behind it — `arch-design` reports unreachable code as *suspected* and
  hands it over rather than calling it dead by eye.
- Reversibility stops re-teaching `PHILOSOPHY.md`'s fifth habit and keeps only what is
  architecture's: which doors are one-way.

`arch-design` goes 188 → 166 lines with nothing dropped — every cut line is said once, in the
skill that owns it.

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
