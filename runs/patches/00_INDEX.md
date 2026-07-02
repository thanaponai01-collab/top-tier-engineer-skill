# Patches for flask_ticket_booking_system (LIVE_RUN_001)

Bounded diffs in the project's own conventions. Each resolves the cited finding(s).
Ordered by blast radius. These are the "diagnosis ships with the artifact" deliverable (Law 5).

| Patch | Resolves | Severity |
|---|---|---|
| 01_auth_server_side_role.md | F1 admin-auth bypass | data/trust — blocker |
| 02_password_hashing.md | F2 reversible passwords | trust — blocker |
| 03_capacity_and_race.md | F3 overbooking + F4 race | money/correctness — blocker |
| 04_schema_fixes.md | F5 unique admits + F6 OR-filter | correctness — major |
| 05_search_and_debug.md | F7 LIKE wildcards + DEBUG=True | availability/RCE-surface — major |
