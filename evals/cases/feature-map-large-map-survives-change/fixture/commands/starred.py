def run(store, args):
    for n in store.all():
        if n['starred']:
            print(f"#{n['id']} {n['title']}")
    return 0
