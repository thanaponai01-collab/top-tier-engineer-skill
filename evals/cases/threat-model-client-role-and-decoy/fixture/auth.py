class User:
    def __init__(self, id, role):
        self.id = id
        self.role = role


# session token -> the user it belongs to, as issued at login
SESSIONS = {
    "tok-customer-1": User(id=1, role="customer"),
    "tok-customer-2": User(id=2, role="customer"),
}


def current_user(session_token):
    return SESSIONS.get(session_token)
