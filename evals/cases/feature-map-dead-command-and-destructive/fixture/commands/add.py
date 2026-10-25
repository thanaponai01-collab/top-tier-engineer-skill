def run(store, args):
    notes = store.all()
    note = {"id": max([n["id"] for n in notes] or [0]) + 1, "title": args.title,
            "body": args.body, "tags": args.tag}
    store.save(notes + [note])
    print(f"added #{note['id']}")
    return 0
