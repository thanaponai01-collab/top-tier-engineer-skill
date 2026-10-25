import json


def render(items):
    return json.dumps(items, indent=2) + "\n"
