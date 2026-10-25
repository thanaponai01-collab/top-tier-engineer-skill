def run(items):
    ids = sorted(i['id'] for i in items)
    return str(sum(b - a - 1 for a, b in zip(ids, ids[1:])))
