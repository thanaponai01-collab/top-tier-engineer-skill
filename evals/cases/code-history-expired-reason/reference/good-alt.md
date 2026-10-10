Short version: it's 60 because of an incident, and the incident's cause has since been fixed, so
the reason has gone away.

`git log -L` on PROFILE_TTL shows it at 5 until 2026-04-14, when a commit raised it to 60 and
pointed at INC-212. The incident doc says team dashboards fetched each member's profile separately,
about 40 reads per page view, and that pushed the profile DB to 100% CPU. A longer cache was the
quick mitigation, and the doc lists batching the dashboard reads as the follow-up.

That follow-up shipped on 2026-07-30: dashboard.py now calls profile.get_many, which loads the whole
team in a single query. So the load the TTL protected against is not there any more, and going back
to 5 s is reasonable. Measure the DB read rate after the change, since nothing in the repo records
current traffic.
