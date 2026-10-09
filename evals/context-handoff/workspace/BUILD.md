# Build

## Next
Define a requirement-backed JSON check for tenant-separated groups containing invoice_id and amount; retain its rejection before implementing. CSV baseline replay is green, but it does not prove the current JSON requirement; complete JSON proof before monthly wiring.

## Evidence state
- 2026-10-09: python check.py => CSV check passed | proven by this session | product baseline 8e5b17cffd452450c627f438840b0937a237b882; handoff notes uncommitted.
- git show confirmed baseline commit; git diff --exit-code 8e5b17c -- exporter.py check.py exited 0. The product files match that commit.
- Current check imports exporter.export and asserts the CSV header for one invoice. Coverage is limited to that CSV success case; JSON grouping and error paths remain unverified.

## Milestones
- [Controlled CSV baseline receipts 0–199](BUILD.archive.md#receipts-0–199): 200 harness repetitions of one check at 8e5b17c, preserved verbatim. Current behavior check: python check.py => CSV check passed (replayed this session). These receipts are not 200 independent features.

## Deferred
- Live email delivery | credentials missing | credentials supplied

## Session handoff — 2026-10-09
JSON accounting intent is current in BRIEF.md; the former CSV intent is retired in BRIEF.archive.md. All active auditing decisions remain in linked brief areas.
Only project notes changed. No product implementation or new commit. The earlier session ran no tests; this continuation replayed the existing CSV check once.
