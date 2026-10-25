"""Messages waiting for the mailer daemon, one JSON object per line."""
import json

from store.db import _path


def enqueue(message):
    with open(_path("outbox.jsonl"), "a", encoding="utf-8") as fh:
        fh.write(json.dumps(message) + "\n")
