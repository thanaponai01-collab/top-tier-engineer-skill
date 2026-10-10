**Short answer:** The 60 was an emergency mitigation for one incident, and the main reason for it has largely been fixed. Dropping to 5 looks much safer than it did, but nobody has measured it yet, so I wouldn't ship it blind.

**Why it's 60** (*proven*, from `git show 7590712` and `docs/incidents/INC-212.md`):
- On 2026-04-13 the profile DB hit 100% CPU and dashboards timed out for about 95 minutes.
- Each team dashboard view did about 40 single-row reads, one per member. At peak that was about 9,000 reads/s against a DB sized for about 1,500.
- The 5 s cache barely helped, because most views were for different teams.
- The fix was to raise the TTL from 5 s to 60 s, which cut reads about 10x. The incident doc lists batching the dashboard reads (owner: Priya) as the follow-up.

**Does it still stand?** Mostly no (*traced*, from `c8e1a6f` and a grep of the callers):
- The follow-up shipped on 2026-07-30. `dashboard.render` now calls `profile.get_many`, which fetches all missing members in one query. That's about 1 query per view instead of about 40, so the load the TTL was hiding is much lower.
- Only two code paths read profiles. `dashboard.py` uses `get_many`, and `settings_page.py` uses `get(user_id)` for one user.

**What I haven't checked:**
- **Load at TTL=5.** The old peak was 9,000 reads/s. Batching cuts that by roughly 40x only if the queries are cheap. A single `fetch_many` of about 40 ids may still cost more than 40 cached lookups. With a 5 s TTL and mostly different teams, nearly every view will miss the cache and run that query. I can't see `fetch_many`'s real cost, because `db.py` is stubbed here. Someone should check production numbers or load-test at 5 s before the change.
- **Whether the TTL will meet product's goal.** `_cache` is a per-process dict. With several workers, a user could see an old profile for up to 5 s on one worker and a fresh one on another. TTL=5 gives "within a few seconds" only if "a few" means up to about 5 s.
- **The user's own edits.** `settings_page` reads through the same cache, so after saving, the editor may see their old profile for up to a TTL. Nothing in this repo invalidates the cache on write. If the real complaint is that people don't see their own edits, invalidating on write (or bypassing the cache for the user's own profile) fixes that without touching the TTL.

**Recommendation:** Lower the TTL, but first confirm the profile DB has headroom for roughly one `fetch_many` per dashboard view at peak traffic. Roll it out gradually, with 60 as the rollback. If the DB can't take it, try a middle value like 15 s, or invalidate on write.