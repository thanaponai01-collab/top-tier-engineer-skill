"""Messages for the mailer daemon."""
from depot import outbox


def build_digest(rows):
    low = [r for r in rows if r["qty"] < 5]
    return {"to": "floor-leads", "subject": f"{len(low)} bins low", "body": ", ".join(str(r["id"]) for r in low)}


def send_digest(rows):
    outbox.enqueue(build_digest(rows))
