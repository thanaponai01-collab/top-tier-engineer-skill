def run(store, args):
    import json
    print(json.dumps(store.all(), indent=2))
    return 0
