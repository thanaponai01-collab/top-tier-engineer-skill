"""Drop outbox lines the mailer has already sent."""
import json

from store.db import _path


def run():
    path = _path("outbox.jsonl")
    try:
        lines = open(path, encoding="utf-8").read().splitlines()
    except FileNotFoundError:
        return
    keep = [l for l in lines if not json.loads(l).get("sent")]
    with open(path, "w", encoding="utf-8") as fh:
        fh.write("".join(l + "\n" for l in keep))
