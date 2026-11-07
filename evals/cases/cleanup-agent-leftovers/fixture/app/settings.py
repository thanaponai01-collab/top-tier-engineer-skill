import json


def get_settings(path="config.json"):
    """Read the app settings."""
    settings = {"data": "data/ledger.json", "currency": "USD"}
    with open(path, encoding="utf-8") as fh:
        settings.update(json.load(fh))
    return settings
