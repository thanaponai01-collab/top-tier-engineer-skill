import datetime as dt


def today():
    return dt.date.today().isoformat()


def age_days(iso, now=None):
    return ((now or dt.date.today()) - dt.date.fromisoformat(iso)).days
