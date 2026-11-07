import json

import requests

RATES_URL = "https://api.frankfurter.app/latest"


def fetch(base):
    resp = requests.get(RATES_URL, params={"from": base}, timeout=10)
    resp.raise_for_status()
    return json.loads(resp.text)["rates"]
