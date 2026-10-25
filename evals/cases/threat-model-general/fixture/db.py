"""In-memory data. A real deployment swaps this for Postgres behind the same functions."""


class User:
    def __init__(self, id, username, password, role="customer", credit=0.0):
        self.id = id
        self.username = username
        self.password = password
        self.role = role
        self.credit = credit


class Invoice:
    def __init__(self, id, owner_id, amount, lines):
        self.id = id
        self.owner_id = owner_id
        self.amount = amount
        self.lines = lines


USERS = {}       # lowercased username -> User
INVOICES = {}    # id -> Invoice


def reset():
    USERS.clear()
    INVOICES.clear()
    USERS["alice"] = User(1, "alice", "alice-pw", credit=50.0)
    USERS["bob"] = User(2, "bob", "bob-pw", credit=5.0)
    USERS["sam"] = User(3, "sam", "sam-pw", role="staff")
    INVOICES[100] = Invoice(100, 1, 42.50, [("widget", 2), ("gadget", 1)])
    INVOICES[101] = Invoice(101, 2, 9.99, [("widget", 1)])


def user_by_id(uid):
    for u in USERS.values():
        if u.id == uid:
            return u
    return None


reset()
