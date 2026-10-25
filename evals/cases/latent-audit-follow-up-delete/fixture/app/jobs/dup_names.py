def run(items):
    names = [i['name'] for i in items]
    return ', '.join(sorted({n for n in names if names.count(n) > 1})) or '-'
