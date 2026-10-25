from depot import notify, store


def run():
    rows = store.load("bins")
    notify.build_digest(rows)
    print(f"digest: {len(rows)} bins checked")
