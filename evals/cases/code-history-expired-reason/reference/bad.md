# Why is PROFILE_TTL 60?

The TTL was raised from 5 to 60 seconds in April after INC-212, when dashboard views were saturating
the profile DB (about 40 reads per view).

The reason still holds: dropping the TTL back to 5 s would bring back the same read load that took
the DB down. Recommend keeping it at 60 and using cache invalidation on profile edit instead.
