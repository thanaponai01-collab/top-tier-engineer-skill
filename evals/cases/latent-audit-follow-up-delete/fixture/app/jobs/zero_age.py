from app.util.dates import age_days


def run(items):
    return str(sum(1 for i in items if age_days(i['added']) == 0))
