**Why it's 60:** INC-212 (2026-04-13). Every team dashboard view did about 40 individual profile reads. At peak that was about 9,000 reads/s against a DB sized for about 1,500, and the DB hit 100% CPU. The TTL was 5 s then, and it barely helped because most views were for different teams. Commit `7590712` raised it to 60 s as a mitigation, cutting reads about 10x. The incident doc (`docs/incidents/INC-212.md`) calls it a stopgap and lists a follow-up to batch the dashboard's reads.

**Does it still stand? Mostly no, but I can't confirm that from the repo.**
- The follow-up shipped in `c8e1a6f` (2026-07-30). `dashboard.render` now calls `profile.get_many`, which fetches all cache-missing members in one query. That is about 1 query per view instead of about 40, so the load that caused the incident should be much lower.
- The 60 s TTL is a leftover mitigation that nobody revisited after the batching. Nothing in the code needs it for correctness.

**What I can't tell from the repo:**
- **Row load:** `get_many` still reads every missing row. With most views hitting different teams, cache misses stay high. Batching cuts query count and round trips, but it doesn't necessarily cut rows read or DB CPU by 40x. The incident doc only gives reads/s, not what the DB can sustain in rows/s.
- **Current traffic:** the doc's numbers are from April. I'd want current peak views/s and DB headroom before going to 5 s. Going back to 5 s is the exact configuration that failed, though with batched reads.

**Another way to get fresh edits:** the settings page uses `profile.get`, and nothing invalidates the cache on write. A user who edits their profile still sees stale data for up to the TTL. Product's "edits show up within seconds" may not need a global TTL change at all. You could evict `_cache[user_id]` on save, which fixes the editor's own view and any view served by the same process. The cache is per-process, so other instances would still wait out the TTL. Dashboards viewed by other people could stay at 60 s, or at a middle value such as 15 s.

**Recommendation:** don't drop it straight to 5 s. Ask Priya (the follow-up owner) or whoever owns the DB for current peak views/s and rows/s headroom. Then either load-test `get_many` at TTL 5, or add invalidate-on-write and keep 60 s. I can write the invalidation if you want it.