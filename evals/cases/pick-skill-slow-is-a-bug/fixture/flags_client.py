import net
import settings

DEFAULTS = {"new_nav": False, "dark_mode": False}


def fetch_flags():
    for _ in range(settings.FLAGS_RETRIES):
        try:
            return net.get_json(settings.FLAGS_URL, timeout=settings.FLAGS_TIMEOUT_S)
        except net.Timeout:
            continue
    return dict(DEFAULTS)
