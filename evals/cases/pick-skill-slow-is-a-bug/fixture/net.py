"""Network shim for this copy: known hosts answer instantly; anything else hangs until the
timeout, the way an unresolvable internal name behaves behind our resolver."""
import time
from urllib.parse import urlsplit

KNOWN_HOSTS = {"flags.internal.example", "metrics.internal.example"}


class Timeout(Exception):
    pass


def get_json(url, timeout):
    host = urlsplit(url).hostname
    if host not in KNOWN_HOSTS:
        time.sleep(timeout)
        raise Timeout(f"{host}: no answer in {timeout}s")
    return {"new_nav": True, "dark_mode": False}
