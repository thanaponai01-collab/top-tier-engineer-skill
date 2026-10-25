import json


def render(rows):
    return json.dumps(rows, indent=1)
