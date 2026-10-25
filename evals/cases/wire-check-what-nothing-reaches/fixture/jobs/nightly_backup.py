import shutil

from store.db import _path


def run():
    try:
        shutil.copy(_path("orders.json"), _path("orders.bak.json"))
    except FileNotFoundError:
        pass
