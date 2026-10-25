def run(store, args):
    notes = store.all()
    archived = [n for n in notes if n['archived']]
    print(f'notes {len(notes)}')
    print(f'archived {100 * len(archived) // len(notes)}%')
    print(f"tags per note {sum(len(n['tags']) for n in notes) / len(notes):.1f}")
    return 0
