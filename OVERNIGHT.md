# Overnight run: agent-friendly consolidation

Contract lives in RUN.json (frozen). Summary, so a stranger can tell when this is done or stopped:

- Goal: a fresh agent finds what the repo is, where facts live, what is next; each skill list/flow
  has one home; merge candidates recorded with a verdict.
- Exit check: `python plugin/skills/drive/scripts/run.py --repo . finish` (stages: tests.test_agent_context, then full suite).
- Budget: 6 attempts total, 4 hours. Two failed attempts on one idea: re-observe, then park.
- Off limits: skill behaviour (SKILL.md procedures), evals/cases, hooks, tests other than the new one
  (except test files that assert the README table/flows I move).
- Authority: local branch `consolidate-skills-agent-context` only. NO push, merge, release, version bump,
  and NO skill rename/removal/merge (skill names and /commands are the public interface).
- Baseline: 476 tests green, catalog 36 skills 5000/5000 chars (before any change).

## Decisions

DECISION: Re-initialised RUN.json once; stage command is now `unittest discover tests -p test_agent_context.py`.
OPTIONS:  Patch the test's sys.path (changes the frozen oracle); keep failing.
WHY:      First contract used `unittest tests.test_agent_context`, which cannot import `_helpers` outside discover. My contract error [proven: ImportError]. Attempt 1 of the original 6 was spent, so the new budget is 5 (total 6). The test file is unchanged.
UNDO:     Not needed; the first run's RUN.json is kept in the scratchpad.

DECISION: Generated the README skill table from frontmatter `card` instead of keeping hand-written prose rows.
OPTIONS:  Keep rows and only dedupe flows; generate from `description`.
WHY:      CLAUDE.md made the README row a manual step that tests only name-check, and the cards are the same text a fresh session already sees [traced: tools/catalog.py]. Per-skill detail still lives in each SKILL.md.
UNDO:     `git checkout main -- README.md tools/catalog.py`.

DECISION: No skill was merged, renamed or removed.
OPTIONS:  Merge drive-overnight into drive, latent-audit+structure-gate, arch-map into arch-design, project-context+project-update.
WHY:      Measured text overlap between every suspect pair is 0.7-6.4% [proven: shingle count], so a merge removes no text; it only changes public names/commands, which the contract does not authorise. Parked with reasoning in docs/merge-proposals.md.
UNDO:     n/a.

DECISION: Moved BUILD.md release history to BUILD.archive.md rather than deleting it.
OPTIONS:  Delete (CHANGELOG has releases); keep.
WHY:      The history holds evidence paths CHANGELOG lacks [traced: compared sections]; archive is the memory convention's home and is not loaded at start.
UNDO:     `git checkout main -- BUILD.md; rm BUILD.archive.md`.

## Morning report
VERDICT:   passed. `run.py finish` -> RUN: complete (484 tests OK, catalog current, 4 of 5 attempts used incl. the contract fix).
DONE:      README table generated; flows have one home; README 3012 -> 1873 words; BRIEF/BUILD/AGENTS.md current; merge analysis in docs/merge-proposals.md [proven].
NEEDS YOU: Skill merges (public names): drive-overnight into drive; latent-audit + structure-gate; arch-map into arch-design; project-context + project-update. Say which, then do the steps in docs/merge-proposals.md.
           Release (not done): version bump + CHANGELOG entry; push/merge of branch consolidate-skills-agent-context.
           Live evals for the changed entry files (cost account usage): `python evals/run.py --cases project-foundation-after-setup`.
DECIDED:   see Decisions above; none rests on a suspected fact.
FAILED:    Attempt 1: wrong test command in my own contract (ImportError). Attempt 2: old test asserted the hand-table message; updated for the generated table.
NEXT:      Decide the four parked merges.
