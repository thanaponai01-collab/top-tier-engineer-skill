from app.util.old_format import normalize


def run(items):
    return str(len({normalize(i['name']) for i in items}))
