from app.util.dates import age_days


def run(items):
    stale = [i["name"] for i in items if i["qty"] == 0 and age_days(i["added"]) > 365]
    return f"would prune {len(stale)}: {', '.join(stale) or '-'}"
