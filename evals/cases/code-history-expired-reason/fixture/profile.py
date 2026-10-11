"""Profile service: reads profiles from the profile DB, with a small cache in front."""
import time

from db import profile_db

PROFILE_TTL = 60  # seconds
_cache = {}


def get(user_id):
    hit = _cache.get(user_id)
    if hit and time.time() - hit[0] < PROFILE_TTL:
        return hit[1]
    row = profile_db.fetch_one(user_id)
    _cache[user_id] = (time.time(), row)
    return row


def get_many(user_ids):
    """One query for many users; fills the cache as it goes."""
    now = time.time()
    missing = [u for u in user_ids if not (_cache.get(u) and now - _cache[u][0] < PROFILE_TTL)]
    for row in profile_db.fetch_many(missing):
        _cache[row["id"]] = (now, row)
    return [_cache[u][1] for u in user_ids]
