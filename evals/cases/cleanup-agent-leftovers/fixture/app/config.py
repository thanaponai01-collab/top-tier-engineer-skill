import json

DEFAULTS = {"data": "data/ledger.json", "currency": "USD"}


def load_config(path="config.json"):
    with open(path, encoding="utf-8") as fh:
        cfg = dict(DEFAULTS)
        cfg.update(json.load(fh))
    return cfg
