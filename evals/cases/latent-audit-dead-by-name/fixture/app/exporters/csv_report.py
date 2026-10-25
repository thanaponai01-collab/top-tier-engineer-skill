import csv, io


def render(items):
    out = io.StringIO()
    w = csv.DictWriter(out, fieldnames=["id", "name", "qty", "added"], lineterminator="\n")
    w.writeheader()
    w.writerows(items)
    return out.getvalue()
