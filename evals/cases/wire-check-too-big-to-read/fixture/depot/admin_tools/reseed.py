from depot import store


def run(args):
    for name in args or ["bins"]:
        store.save(name, store.seed(name))
    print("reseeded " + ", ".join(args or ["bins"]))
