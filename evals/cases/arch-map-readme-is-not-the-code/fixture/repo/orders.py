import db


def fetch_all():
    with db.connect() as conn:
        return conn.execute("SELECT id, sku, qty, total FROM orders").fetchall()


def insert(order):
    with db.connect() as conn:
        cur = conn.execute("INSERT INTO orders (sku, qty) VALUES (?, ?)", (order["sku"], order["qty"]))
        return cur.lastrowid
