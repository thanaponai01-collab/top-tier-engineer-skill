def run(store, args):
    import csv
    notes = store.all()
    nid = max((n['id'] for n in notes), default=0)
    with open(args.path, encoding='utf-8') as fh:
        for row in csv.DictReader(fh):
            nid += 1
            notes.append({'id': nid, 'title': row['title'], 'body': row['body'], 'tags': [t for t in row['tags'].split(';') if t],
                          'archived': False, 'pinned': False, 'starred': False, 'due': None, 'created': '2026-10-25'})
    store.save(notes)
    print(f'imported up to #{nid}')
    return 0
