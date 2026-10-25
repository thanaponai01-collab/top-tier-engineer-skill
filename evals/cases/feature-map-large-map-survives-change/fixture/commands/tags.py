def run(store, args):
    counts = {}
    for n in store.all():
        for t in n['tags']:
            counts[t] = counts.get(t, 0) + 1
    for t, c in sorted(counts.items()):
        print(f'{t} {c}')
    return 0
