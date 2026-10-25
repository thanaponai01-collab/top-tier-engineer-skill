from app.util.old_format import normalize


def run(items):
    index = {normalize(i['name']): i['id'] for i in items}
    return f"indexed {len(index)}"
