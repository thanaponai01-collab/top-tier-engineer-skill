from core.util import clamp


PREFS = {}


def set_pref(cid, key, value):
    PREFS.setdefault(cid, {})[key] = value


def get_pref(cid, key, default=None):
    return PREFS.get(cid, {}).get(key, default)


def digest_hour(cid):
    return clamp(get_pref(cid, 'digest_hour', 8), 0, 23)
