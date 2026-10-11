def run(store, args):
    if not args.yes:
        print("refusing without --yes")
        return 1
    store.save([])
    print("all notes deleted")
    return 0
