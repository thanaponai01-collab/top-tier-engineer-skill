WHY: `PROFILE_TTL` is 60 s because dashboards were melting the profile DB in April.
BECAUSE: INC-212: each team-dashboard view read about 40 profiles one by one and saturated the profile DB
(100% CPU). The 5 s cache barely helped, so the TTL was raised to 60 s as the mitigation. [traced]
(commit "Raise profile cache TTL to 60s", 2026-04-14; `docs/incidents/INC-212.md`)
INSTEAD OF: batching the reads, recorded in the incident as the follow-up.
STILL HOLDS: **no, expired.** The follow-up landed on 2026-07-30 ("Dashboard: one profile query per
view"): `dashboard.render` now calls `profile.get_many`, one query per view instead of about 40. The
load the 60 s TTL was protecting against is gone. [traced: `git log -p -- dashboard.py profile.py`]
NOT CHECKED: no issue tracker, chat or metrics connected. Today's DB read rate isn't measured, so
check reads/s at the new TTL before calling it safe.

Recorded in `WHY.md`.
