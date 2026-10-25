def run(store, args):
    notes = store.all()
    nid = max((n['id'] for n in notes), default=0) + 1
    notes.append({'id': nid, 'title': args.title, 'body': args.body, 'tags': args.tag, 'archived': False,
                  'pinned': False, 'starred': False, 'due': None, 'created': '2026-10-25'})
    store.save(notes)
    print(f'added #{nid}')
    return 0
