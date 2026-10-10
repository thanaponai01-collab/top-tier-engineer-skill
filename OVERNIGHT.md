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
