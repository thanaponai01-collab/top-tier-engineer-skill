import sqlite3

from settings import DB_PATH


def connect():
    return sqlite3.connect(DB_PATH)
