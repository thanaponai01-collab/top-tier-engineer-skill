**Verdict:** The 60 was a mitigation for an outage (INC-212), and the dashboard change it was waiting on has since shipped. So the reason has probably expired, but nothing in the repo measures whether 5 s is now safe.

```
WHY: PROFILE_TTL was raised from 5 to 60 as an emergency mitigation for INC-212, not as a freshness choice.
BECAUSE: On 2026-04-13 the dashboard did ~40 individual profile reads per view, peaking at ~9,000 reads/s against a DB sized for ~1,500. The 5 s cache barely helped because most views were for different teams. 60 s was expected to cut reads ~10x. [proven: I read the commit and the incident doc] (7590712, docs/incidents/INC-212.md)
INSTEAD OF: The incident doc names one alternative, batching the dashboard reads (owner: Priya), as the follow-up rather than a substitute. It shipped in c8e1a6f (2026-07-30) as `profile.get_many`, one query per view.
STILL HOLDS: probably expired, cannot tell for certain.
```

**Why it probably expired [traced]:**
- The original trigger was 40 queries per view. `dashboard.py` now makes 1 per view, so the query rate on a full cache miss is about 40x lower. That is ~225 queries/s at the incident peak against ~1,500 capacity.
- That only helps if the DB's limit is queries, not rows. `get_many` still reads the same ~40 rows per view. If the limit is row-bound, the 9,000/s figure comes back at TTL 5.
- Nothing in the repo shows load after c8e1a6f. No metrics, no load test, no follow-up note.
- Going from 60 to 5 would raise DB reads ~12x at the same hit pattern, which is the same direction as the original incident.

**Related to the product ask [traced]:**
- Nothing invalidates the cache on write. `settings_page.py` calls `profile.get`, so a user's own edit shows up late in their own settings page, for up to `PROFILE_TTL` seconds. I found no write path in the repo.
- Evicting that user's entry when a profile is written would make edits show immediately without changing the TTL. Dashboards would then lag only for other people's edits.

**Before changing it:** get the profile DB's current load (QPS and CPU) from observability, or load-test `get_many` at peak with TTL 5. Then roll out in steps, such as 60 → 15 → 5, while watching DB CPU.

**Not checked:** I had no issue tracker, chat, observability, or analytics access. The only sources were the git history (4 commits) and `docs/`. I didn't write `WHY.md`, since the digging was short.