def run(items):
    for i in items:
        i.setdefault('added', '2024-01-01')
    return 'backfilled'
