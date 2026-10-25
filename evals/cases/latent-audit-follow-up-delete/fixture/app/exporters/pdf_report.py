from app.util.old_format import normalize


def render(items):
    lines = [f"{i['id']:>4} {normalize(i['name']):<20} {i['qty']:>6}" for i in items]
    return "%PDF-1.1 (text)\n" + "\n".join(lines) + "\n"
