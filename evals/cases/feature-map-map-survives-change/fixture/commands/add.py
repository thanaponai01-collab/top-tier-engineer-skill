def run(store, args):
    notes = store.all()
    note = {"id": store.next_id(), "title": args.title, "body": args.body, "tags": args.tag}
    notes.append(note)
    store.save(notes)
    print(f"added #{note['id']}")
    return 0
