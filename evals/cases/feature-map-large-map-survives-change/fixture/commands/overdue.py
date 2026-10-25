def run(store, args):
    for n in store.all():
        if n['due'] and n['due'] < args.today:
            print(f"#{n['id']} {n['title']} (due {n['due']})")
    return 0
