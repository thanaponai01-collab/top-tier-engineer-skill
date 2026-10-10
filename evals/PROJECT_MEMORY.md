# Project memory validation

## Implemented
Two discoverable skills, file-backed context with a disposable SQLite/FTS index, bounded read-only
retrieval, incremental transactional indexing, fallback/rebuild, context structural checks,
compact startup output and upkeep instructions across all existing skills.

## Checks executed
- python -m unittest discover tests: 444 tests passed (102.016 seconds).
- Final helper adjustment: 14 focused project-context tests passed.
- Catalog: 35 skills; listing 4954/5000 characters; every copy current.
- Both new SKILL.md files passed quick_validate.py.
- Context budget/handoff checker: no overruns or structural gaps.
- CLI exercised against this worktree: index, rebuild, search, targeted update and check.
- git diff --check: clean.

## Cost experiment
Synthetic 5,000-section Markdown history; one local run, not an AI latency benchmark.
- Index: 0.9516 seconds.
- Search: 0.0099 seconds; 5 results, 1303 output bytes.
- No-op upkeep of one selected file: 0.0027 seconds.

Tests also demonstrate that incremental indexing reads only selected files and query freshness
checks read each matching source once. The index searches selected context, not all source code.

## Behavioral validation limitation
Both without-skill and with-skill agent runs returned Claude's session usage limit before doing
work. Retained reports live in results/project-memory-baseline and results/project-memory-with.
These are runner failures, not evidence that the baseline fails or that the skills help.
Cases were finalized after the attempt; rerun both arms for the final cases and the affected
existing-skill regressions before release. No release or installed-plugin update was performed.

## Reproduce
python evals/run.py --cases project-context-stale-evidence project-update-preserves-intent --repeats 1 --jobs 1

## Limits
A cached query cannot discover new unindexed text; upkeep must index changed context records.
Path associations do not replace dependency/caller tracing. Structural checks cannot prove user
intent, test correctness or that every agent follows upkeep. Missing indexes fall back to at most
50 files; full discovery is bounded to 500 and reports truncation. Larger stores use explicit areas.

## Complete foundation refresh
- project-setup prepares all categories by default and defers verification detail to a reference.
- onboard-system reuses setup; architecture changes update affected boundaries rather than all code.
- agents/setup-reader.md is read-only and configured for Haiku; host overrides/availability apply.
- Foundation helper inventories equivalent paths, checks structural completeness and remembers
  scoped input hashes without treating them as product evidence.
- Full suite: 452 tests passed in 111.881 seconds; focused foundation 7 and context 15 tests passed.
- Claude native validators accepted skills and agents; Codex's standalone validator rejects the
  existing Claude-specific disable-model-invocation field, so native validation was used.
- Full-foundation/old-setup/project-update live evaluations: six attempts with Haiku hit the account
  usage limit before doing work. Results: results/full-foundation-refresh. No behavioral pass claimed.
- Current architecture: docs/architecture.md. Key commands: docs/commands.md.
