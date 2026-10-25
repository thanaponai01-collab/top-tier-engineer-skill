import json


def run(store, args):
    with open(args.path, "w") as fh:
        json.dump(store.all(), fh, indent=2)
    print(f"exported to {args.path}")
    return 0
