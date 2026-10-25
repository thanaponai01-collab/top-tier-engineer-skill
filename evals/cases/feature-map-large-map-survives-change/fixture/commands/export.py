def run(store, args):
    import csv
    with open(args.path, 'w', newline='', encoding='utf-8') as fh:
        w = csv.writer(fh)
        w.writerow(['id', 'title', 'body', 'tags'])
        for n in store.all():
            w.writerow([n['id'], n['title'], n['body'], ';'.join(n['tags'])])
    print(f'exported to {args.path}')
    return 0
