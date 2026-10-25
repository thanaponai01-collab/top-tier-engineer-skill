"""Keep the audit log to its last 10,000 lines."""
from depot.store import _path


def run():
    try:
        with open(_path("audit"), encoding="utf-8") as fh:
            lines = fh.readlines()
    except FileNotFoundError:
        return
    with open(_path("audit"), "w", encoding="utf-8") as fh:
        fh.writelines(lines[-10000:])
