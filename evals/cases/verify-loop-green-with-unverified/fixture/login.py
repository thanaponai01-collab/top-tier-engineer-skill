USERS = {"demo@example.com": "s3cret"}


def login(email, password):
    return USERS.get(email) == password
