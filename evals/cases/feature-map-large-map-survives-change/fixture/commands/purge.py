def run(store, args):
    import os
    if not args.yes:
        print('refusing without --yes')
        return 1
    with open(os.path.join(os.path.dirname(store.PATH), 'purge.log'), 'a', encoding='utf-8') as fh:
        fh.write('purged all notes\n')
    store.save([])
    print('all notes deleted')
    return 0
