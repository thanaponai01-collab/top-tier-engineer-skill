from zoneinfo import ZoneInfo


def to_local(moment, tz_name):
    """An aware datetime shown in the traveller's zone (names like 'Asia/Bangkok')."""
    return moment.astimezone(ZoneInfo(tz_name))
