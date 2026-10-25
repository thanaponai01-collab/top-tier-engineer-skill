def run(store, args):
    notes = store.all()
    for n in notes:
        if n["id"] == args.id:
            if args.name not in n["tags"]:
                n["tags"].append(args.name)
            store.save(notes)
            print(f"tagged #{args.id} {args.name}")
            return 0
    print(f"no note #{args.id}")
    return 1
