"""Core commands: add, list, show, search, tag, export, purge, debug-dump."""
import csv, json, os


def add(store, args):
    notes = store.all()
    nid = max((n["id"] for n in notes), default=0) + 1
    notes.append({"id": nid, "title": args.title, "body": args.body, "tags": args.tag})
    store.save(notes)
    print(f"added #{nid}")
    return 0


def list_(store, args):
    for n in store.all():
        if args.tag is None or args.tag in n["tags"]:
            print(f"#{n['id']} {n['title']}")
    return 0


def show(store, args):
    n = next((n for n in store.all() if n["id"] == args.id), None)
    if n is None:
        print(f"no note #{args.id}")
        return 1
    print(json.dumps(n, indent=2))
    return 0


def search(store, args):
    q = args.query.lower()
    for n in store.all():
        if q in n["title"].lower() or q in n["body"].lower():
            print(f"#{n['id']} {n['title']}")
    return 0


def tag(store, args):
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


def export(store, args):
    with open(args.path, "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["id", "title", "body", "tags"])
        for n in store.all():
            w.writerow([n["id"], n["title"], n["body"], ";".join(n["tags"])])
    print(f"exported to {args.path}")
    return 0


def purge(store, args):
    if not args.yes:
        print("refusing without --yes")
        return 1
    with open(os.path.join(os.path.dirname(store.PATH), "purge.log"), "a", encoding="utf-8") as fh:
        fh.write("purged all notes\n")
    store.save([])
    print("all notes deleted")
    return 0


def debug_dump(store, args):
    print(json.dumps(store.all(), indent=2))
    return 0
