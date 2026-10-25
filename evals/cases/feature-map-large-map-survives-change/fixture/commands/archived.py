def run(store, args):
    for n in store.all():
        if n['archived']:
            print(f"#{n['id']} {n['title']}")
    return 0
