**WHY:** `PROFILE_TTL` went from 5 to 60 as an emergency fix for incident INC-212, when the profile DB saturated.

**BECAUSE:** On 2026-04-13 the team dashboard read each member's profile separately, about 40 reads per view. At peak that was about 9,000 reads/s against a DB sized for about 1,500, and dashboard loads timed out from 09:40 to 11:15. The 5 s cache barely helped because most views were for different teams. Raising the TTL to 60 s was meant to cut reads about 10x. [traced] (`7590712`, `docs/incidents/INC-212.md`)

**INSTEAD OF:** The incident doc names one alternative, batching the dashboard's reads. It was listed as a follow-up (owner: Priya), and the TTL bump was the stopgap until then.

**STILL HOLDS:** Mostly no. The follow-up shipped in `c8e1a6f` (2026-07-30). `dashboard.render` now calls `profile.get_many`, which makes one query per view, and only for members not already cached. The 40x fan-out that justified 60 s is gone. [traced]

- **Rough headroom:** 9,000 reads/s ÷ 40 is about 225 queries/s, against about 1,500 capacity. That assumes April's traffic and that a query costs about the same however many rows it returns. [suspected]
- **Not shown:** There's no measurement of the DB after the batching change, and no current traffic figure. Nothing in the record says 5 s is safe, only that the original reason has mostly expired.

**Why it matters for product:** `settings_page.py` reads through `profile.get`. Nothing invalidates the cache on write, so a user can see their own edit as stale for up to 60 s.

**Suggestion:** Before dropping the TTL to 5, load-test `get_many` at current peak dashboard traffic, or check DB metrics since July 30. If you only need the edit to show up on the settings page, invalidate that user's cache entry on write. That fixes the complaint without changing the TTL for dashboard reads.

**NOT CHECKED:** I only had git and the repo's `docs/`. I didn't have an issue tracker, chat, monitoring or analytics, so I couldn't check the current load or the DB's post-July behavior. The cache is per process, so I also didn't check how many processes there are.

I didn't write a `WHY.md` entry. Say if you want one.