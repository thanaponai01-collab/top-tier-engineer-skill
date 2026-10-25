def run(store, args):
    import datetime
    today = datetime.date.fromisoformat(args.today)
    end = today + datetime.timedelta(days=args.days)
    for n in store.all():
        if n['due'] and today <= datetime.date.fromisoformat(n['due']) <= end:
            print(f"#{n['id']} {n['title']} (due {n['due']})")
    return 0
