"""Five commands for the `version` field of a note: set-version, clear-version, by-version, count-version, show-version."""


FIELD = "version"


def _find(notes, nid):
    return next((n for n in notes if n["id"] == nid), None)


def parse(value):
    return value.strip()


def set_(store, args):
    notes = store.all()
    n = _find(notes, args.id)
    if n is None:
        print(f"no note #{args.id}")
        return 1
    n[FIELD] = parse(args.value)
    store.save(notes)
    print(f"#{n['id']} {FIELD} = {n[FIELD]}")
    return 0


def clear(store, args):
    notes = store.all()
    n = _find(notes, args.id)
    if n is None:
        print(f"no note #{args.id}")
        return 1
    n[FIELD] = None
    store.save(notes)
    print(f"#{n['id']} {FIELD} cleared")
    return 0


def by(store, args):
    want = parse(args.value)
    for n in store.all():
        if n.get(FIELD) == want:
            print(f"#{n['id']} {n['title']}")
    return 0


def count(store, args):
    counts = {}
    for n in store.all():
        counts[n.get(FIELD)] = counts.get(n.get(FIELD), 0) + 1
    for value, c in sorted(counts.items(), key=lambda kv: str(kv[0])):
        print(f"{value} {c}")
    return 0


def show(store, args):
    n = _find(store.all(), args.id)
    if n is None:
        print(f"no note #{args.id}")
        return 1
    print(f"#{n['id']} {FIELD}: {n.get(FIELD)}")
    return 0
