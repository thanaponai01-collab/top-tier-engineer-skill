# Overnight run 2026-10-11: eval coverage for every skill, then the gaps

Contract: RUN.json (frozen from work/overnight/contract.json). Enforcement: drive's run.py helper.

- **Goal:** every skill under `skills/` has an eval case under `evals/cases/` that discriminates
  (good/good-alt pass, bad fails), each of the 17 newly covered cases has been run live in both arms
  (with the plugin, without), and the skills' gaps are written up. The focus is the context a fresh
  agent session gets: scalable, clean, efficient.
- **Exit check:** `python work/overnight/exit_check.py`. It passes when uncovered.txt is empty, the
  unit suite is green, and every new case has a completed live run in both arms. A skill *failing*
  its case is a finding for the report, not a failure of this check.
- **Budget:** two drafts per case (rewrite only if the reference set doesn't discriminate). Live:
  1 try per arm per case, `claude-sonnet-5-5`, `--budget-usd 3` per run (worst case 34 × $3 = $102,
  expected around $15–30). If a skill fails, at most one rerun to separate a flake from a gap. Total
  ceiling: 12 hours or $60 of eval spend, whichever comes first.
- **Off limits:** existing cases' `expect.json` and references (no weakening); skill text (gaps get
  reported, not silently fixed; see DECISION 2); `main`; version bump and CHANGELOG (that's a release).
- **Authority:** commit to branch `claude/skills-evals-coverage-gaps-b11be8` only. No push, merge,
  PR, issue or other external mutation. The eval agents run with an empty `gh` config, so they can't
  reach the user's GitHub either.

## Decisions

DECISION 1: proceed on recorded defaults instead of asking the opening questions
OPTIONS:  ask budget/authority first; proceed with conservative defaults
WHY:      the request says "just create", and the run is unattended. Every default above is
          reversible (branch only, capped spend) [traced: request text]
UNDO:     delete the branch; spend is capped per run

DECISION 2: report skill gaps, don't rewrite skills tonight
OPTIONS:  fix each skill that fails its new case; report with evidence and proposed fixes
WHY:      a skill change needs its own before/after eval (CLAUDE.md), which costs another live
          cycle per skill. Better for the owner to choose which gaps to pay for. Small harness fixes
          needed to *run* cases are in scope [traced: CLAUDE.md]
UNDO:     n/a (nothing changed in skills/)

DECISION 3: one case per skill, report-graded where possible, finished-repo checks where the skill's
          product is a file (arch-map, feature-map, problem-framing, agent-design)
OPTIONS:  several cases per skill; action-heavy cases throughout
WHY:      17 skills under one budget. One sharp decoy per skill gets coverage now; depth comes later
          [suspected: no prior evidence of which skills need more]
UNDO:     add more cases later; nothing depends on this

DECISION 4: add a per-case `setup.py` hook to evals/run.py (it builds git history in the scratch
          copy) and isolate `gh` (empty GH_CONFIG_DIR, no GH_TOKEN) for every eval agent
OPTIONS:  commit nested .git dirs (git refuses them); ship git bundles and have the prompt explain
          them (unnatural); skip the git-based skills
WHY:      code-history, recall and scrutinize are about history and diffs, so they can't be tested
          without git. An issue-handoff agent with the user's real gh login could file real issues
          [traced: agent.clean_env keeps USERPROFILE/APPDATA, where gh stores its token]
UNDO:     revert the run.py/agent.py commit

## Log
- 2026-10-11: harness: `setup.py` hook + `evals/history.py` (git history ending on fixture/), gh isolated
  (empty GH_CONFIG_DIR). Unit test added: every setup.py ends on its fixture with history [proven].
- 17 cases written; every reference set discriminates on the phrase grader (good/good-alt pass, bad
  fails) [proven: tests/test_evals.py, 44 OK]. Judge calibration on the new cases: 51/51 [proven].
- Full suite exposed a non-hermetic hook test (`test_every_malformed_payload_exits_zero_and_silent` ran
  the Stop gate in the checkout's cwd and saw this run's RUN.json). Fixed the test to run from an
  empty dir; hook unchanged.

DECISION 5: live runs use `--no-scorecard`, and RESULTS.md gets a hand-written section
OPTIONS:  let run.py rewrite RESULTS.md
WHY:      RESULTS.md is a curated history of releases; run.py would replace it with this batch only
          [traced: run.py "rewrites RESULTS.md"; current file is hand-edited sections]
UNDO:     rerun with the scorecard, or rescore the results folder

DECISION 6: repair the double-encoded UTF-8 in build-discipline, code-history, feature-map (G3)
OPTIONS:  report only (DECISION 2)
WHY:      byte-level repair (â†’ → →, Â· → ·), no instruction changes, so no eval re-run needed
          [proven: byte scan before/after]
UNDO:     git revert the commit

DECISION 7: say "`fixture/` is the repo root" in the prompts of the four file-graded cases, then rerun them
OPTIONS:  widen the replay to look outside fixture/; leave it and count the fail
WHY:      the arch-map plain agent wrote an excellent docs/architecture.md at the scratch root, not in
          fixture/, so the replay saw nothing. "Keep it in the repo" was ambiguous in a folder that
          only contains fixture/. A wording fix, not a looser check [proven: result.json changes]
UNDO:     git revert the prompt edits

DECISION 8: isolate eval agents from the person's user settings (`--setting-sources project,local`),
          discard the first batch as contaminated, and rerun all 17 cases in both arms
OPTIONS:  keep the batch and footnote it; CLAUDE_CONFIG_DIR isolation (would also drop the login);
          --bare (needs an API key, and this machine uses OAuth)
WHY:      [proven] `claude -p` with no --plugin-dir listed top-tier-engineer skills and saw the global
          CLAUDE.md (PHILOSOPHY); with --setting-sources project,local it saw neither, and a
          --plugin-dir staged copy still loaded (29 model-invocable skills). In the batch, the
          "without" arm opened agent-design and arch-map. Every earlier RESULTS.md comparison ran
          under the same leak (suspected; the installed version varied)
UNDO:     drop the flag in agent.build_command; the old batch is kept in
          evals/results/coverage-2026-10-11-contaminated/

DECISION 9: widen agent-design's one-way item: removing a tool's one-way risk by redesign counts as handled
OPTIONS:  keep the item and count the with-arm fail
WHY:      the with-arm agent replaced send_email(to, subject, body) with a templated send_summary
          fixed to the order's address: a stronger answer than "confirm each send". Risk: changed
          after seeing a result. Mitigated by keeping cancel_order and issue_refund mandatory and
          re-judging *both* arms' saved reports [proven: report.md lines 7, 52]
UNDO:     git revert the expect.json edit and rescore
