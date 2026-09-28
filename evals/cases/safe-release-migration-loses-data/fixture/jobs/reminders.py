"""Nightly job: text every user a reminder the day before their appointment."""


def recipients(conn):
    return [
        {"name": name, "to": phone}
        for name, phone in conn.execute("SELECT name, phone FROM users WHERE phone IS NOT NULL")
    ]
