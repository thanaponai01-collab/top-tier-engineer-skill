def run(store, args):
    import datetime
    day = datetime.datetime.strptime(args.date, '%Y-%m-%d').date()
    notes = store.all()
    n = next((n for n in notes if n['id'] == args.id), None)
    if n is None:
        print(f'no note #{args.id}')
        return 1
    n['due'] = day.isoformat()
    store.save(notes)
    print(f'#{n["id"]} due {n["due"]}')
    return 0
