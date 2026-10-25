import json


def run(store, args):
    print(json.dumps(store.all(), indent=2))
    return 0
