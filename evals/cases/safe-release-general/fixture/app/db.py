import os
import sqlite3
from contextlib import contextmanager

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def path():
    return os.environ.get("SHOP_DB", os.path.join(HERE, "data", "shop.db"))


@contextmanager
def connect():
    """A connection that commits on success and is always closed."""
    conn = sqlite3.connect(path())
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()
