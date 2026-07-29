# Patches for SUBJECT_A (LIVE_RUN_001)

> **Redacted for publication.** Subject systems appear as `SUBJECT_A` (a Flask + SQLite
> ticket-booking app), `SUBJECT_B` (a graph/memory service), and `SUBJECT_C` (a Next.js +
> Postgres time-tracker); local paths are removed. The redaction changes *identities only* —
> every finding, evidence tag, verdict line and file:line reference is the original. This is
> a publication edit, not a rules edit: PROTOCOL §11's "annotated, never retouched" governs
> retouching a transcript to satisfy a *check*, which nothing here does.

Bounded diffs in the project's own conventions. Each resolves the cited finding(s).
Ordered by blast radius. These are the "diagnosis ships with the artifact" deliverable (Law 5).

| Patch | Resolves | Severity |
|---|---|---|
| 01_auth_server_side_role.md | F1 admin-auth bypass | data/trust — blocker |
| 02_password_hashing.md | F2 reversible passwords | trust — blocker |
| 03_capacity_and_race.md | F3 overbooking + F4 race | money/correctness — blocker |
| 04_schema_fixes.md | F5 unique admits + F6 OR-filter | correctness — major |
| 05_search_and_debug.md | F7 LIKE wildcards + DEBUG=True | availability/RCE-surface — major |
