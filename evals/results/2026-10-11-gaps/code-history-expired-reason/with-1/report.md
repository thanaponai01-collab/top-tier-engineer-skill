Done. I traced the history and saved the result to `WHY.md`. Here's the answer.

**The 60 was an emergency fix for an incident, and the problem it was covering has since been fixed. So the original reason has mostly expired.** It doesn't block going to 5 s, but one number should be measured first.

```
WHY: PROFILE_TTL was raised from 5 s to 60 s on 2026-04-14.
BECAUSE: INC-212. Each dashboard view read ~40 profiles one at a time, about 9,000 reads/s at
  peak against a DB sized for ~1,500. The DB hit 100% CPU and page loads timed out for ~1.5 h.
  A 60 s TTL cut reads ~10x. [traced] (32a0d1d, docs/incidents/INC-212.md)
INSTEAD OF: The incident doc called the TTL bump a mitigation. It named the real fix as a
  follow-up: "batch the dashboard's profile reads".
STILL HOLDS: No, expired. That follow-up shipped in ac9cab3 (2026-07-30): dashboard.render now
  calls profile.get_many, one query per view. At the INC-212 peak (~225 views/s) that is about
  225 queries/s even with no cache hits, well under the ~1,500 the DB is sized for.
NOT CHECKED: Only git and the repo's docs were available here. I had no access to the ticket
  tracker, chat, monitoring or the DB's current load.
```

**What I couldn't confirm:**
- **Cost of a batched query:** whether one 40-row `fetch_many` costs the DB about one read or about 40. If it's closer to 40, going back to 5 s brings back most of the INC-212 load.
- **Current traffic:** what peak traffic is today compared with April.

Before changing the TTL, check the DB's CPU per batched query, or try 5 s in staging under realistic load. At 5 s you'd also be back at the original value, which the incident doc says "barely helped".

**The TTL may not be the right setting to change.** Nothing clears a profile from the cache when it's edited. That means the TTL is both:
- how long the DB is protected, and
- how long the settings page (`profile.get`) can show stale data.

Clearing the edited user's cache entry when they save their profile would make edits show up right away and keep the 60 s protection. One catch: the cache is a dictionary inside each process. With several server processes, an edit only clears the copy in the process that handled it. That needs checking before relying on this fix. Also, this copy of the repo has no code that saves profile edits (`settings_page.py` only displays the profile), so I couldn't see where that change would go.

<!-- file written by the agent: fixture/WHY.md -->
# WHY

Index (`question | label | date`):

- Why is `PROFILE_TTL` in profile.py 60 s? | traced; expired | 2026-10-11

---

## Why is `PROFILE_TTL` in profile.py 60 s?

- **Answer:** It was raised from 5 s to 60 s as the fix for incident INC-212 (2026-04-13). Each team
  dashboard view read about 40 profiles one at a time, which came to about 9,000 reads/s at peak
  against a DB sized for about 1,500. A 60 s TTL cut reads by about 10x. The incident doc calls this
  a mitigation and names the real fix as a follow-up: batch the dashboard reads.
- **Label:** traced.
- **Still holds:** expired. ac9cab3 (2026-07-30) shipped that follow-up: `dashboard.render` now
  calls `profile.get_many`, one query per view. At the INC-212 peak (~225 views/s) that is at most
  ~225 queries/s even with no cache hits. Not measured: how much one 40-row `fetch_many` costs the
  DB compared with 40 single reads, or what peak traffic is today.
- **Instead of:** nothing else was weighed in the record. This was the quick fix; batching was the
  intended permanent one.
- **Sources:** 916548e (introduced, TTL 5), 32a0d1d (TTL 5 → 60),
  docs/incidents/INC-212.md, ac9cab3 (batched dashboard reads).
- **Note:** nothing invalidates the cache when a profile changes, so any TTL is also the staleness
  window for the settings page (`profile.get`).
