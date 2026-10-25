import json

from depot.store import _path


def enqueue(message):
    with open(_path("outbox"), "a", encoding="utf-8") as fh:
        fh.write(json.dumps(message) + "\n")
