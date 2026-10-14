# P09 evidence

This record owns P09 trial details; RUN.json owns the current stage and repository proof state.

## Before-edit behavior baseline

Date: 2026-10-13. Fixture: `evals/cases/drive-program-delivery/`. Model: Claude Sonnet 5.5 in both
arms. One run per arm, $2 per-run cap. After correcting the rubric to require inspection of the
shared persistence boundary, both reports were meaning-judged at 7/8 and missed only that finding.
The with arm recognized that documentation validation depends on A's schema; neither identified
that no slice owns the shared store. Read-only and no-forge-action checks passed. Without: $0.0606,
16.5 seconds. With: $0.0920, 19.8 seconds. Neither arm dispatched workers. This baseline shows no
Drive advantage on the shared-store finding before P09 guidance; one trial is not a reliability or
cost comparison.

Raw reports, action logs, transcripts and judge outputs: [baseline run](../../evals/results/p09-baseline/).
The comparison is a smoke trial for one planning/review task. It does not exercise real forge state,
PR mutation, independent per-PR verification or large-team execution.

## Rejected trial and check correction

The first post-change replay in [the retained output](../../evals/results/p09-final/) passed 8/8
without Drive and 7/8 with Drive, but the case incorrectly rewarded parallelizing C and D without a
named shared-storage owner. The evaluator process also exited zero when the with arm failed. That
run is preserved as failed in [the run archive](../runs/RUN.p09-behavior-gate-failed.json); its
verdict is not acceptance evidence. The corrected case now requires the missing boundary, and the
behavior command checks the retained per-arm pass state before it can exit zero.

## After-edit behavior

The corrected case was run once per arm on 2026-10-13 with Claude Sonnet 5.5 and a $2 per-run cap.
The no-skill control found 7/8 and missed the unowned shared-storage finding ($0.0638, 19.0
seconds). Drive found 8/8, read both `skills/drive/SKILL.md` and the new
`program-delivery.md` reference, passed the read-only and no-forge-action checks, and dispatched no
workers ($0.1034, 22.8 seconds). The retained reports and action evidence are in
[the corrected replay](../../evals/results/p09-verified/). This single fixture shows a bounded
behavior difference on the planted shared-boundary finding; it does not establish reliability,
cost savings, large-team execution or real forge-state accuracy.

The initial post-change replay and its defective check are preserved under
[the failed run](../../evals/results/p09-final/) and [run journal](../runs/RUN.p09-behavior-gate-failed.json).
The corrected acceptance case and replay-safe result check are retained in the repo. Repository
suite and catalog proof are recorded in RUN.json. No external PR actions, installed-plugin update,
release or version change is authorized by this task.

The first retained-result checker run failed on a Windows path separator mismatch; it did not rerun
the agent or invalidate the live evaluation. The failure is preserved in
[the checker run journal](../runs/RUN.p09-evidence-path-failed.json); the checker now normalizes
the action-log path before confirming the new reference was read.

An initial content-check preflight also used literal phrases that were split by line wrapping or
expressed with equivalent wording in the guide. It prompted a check-list correction and an explicit
"contiguous verified prefix" phrase; no live evaluation was rerun for this edit.

The next content-check preflight expected a root-relative evidence path while the handoff correctly
uses a path relative to its own directory. The checker now matches that existing link form.

One more content-check preflight found an assertion split across Markdown line breaks. The final
content checker now normalizes whitespace before matching short required phrases.

The first repository suite run then exposed the startup limit: BUILD.md had 43 lines against the
40-line check. I compacted three blank separators without removing build facts; the run journal
retains the failed suite output.
