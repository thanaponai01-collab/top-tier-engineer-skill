# Recall improvement

On 2026-10-13, clarified `skills/recall/SKILL.md`: corrections belong in the catch-up capsule,
historical receipts are not current passing proof, and missing conventional context filenames
alone do not justify starting onboarding. Owner-stated decisions retain the existing write exception.

Live command: `python evals/run.py --cases recall-stale-proof --repeats 1 --jobs 1`.
Both arms passed (one run each); this does not demonstrate improvement over baseline.
Final clarification replay: `python evals/run.py --cases recall-stale-proof --arms with --repeats 1 --jobs 1`
passed. Evidence: `evals/results/2026-10-13-1146/` and `evals/results/2026-10-13-1147/`.
The replay's `recall-stale-proof/with-1/actions.txt` records a Read of the installed recall SKILL.md;
the generated scorecard's opened-skill count reports zero. Treat that counter as unreliable here.
The existing case exercises stale proof and read-only behavior; missing-document routing is unmeasured.

Catalog check passed. The first full test run had one exact-glossary failure in 484 tests;
the glossary was restored and the full suite rerun: all 484 tests passed (98.839 seconds).
`git diff --check` also passed. These checks cover the local uncommitted revision, not a release.

Next for this skill: add an action-graded missing-document catch-up case that distinguishes useful
Git recovery from automatic onboarding; leave the broader project Next in BUILD.md unchanged.
