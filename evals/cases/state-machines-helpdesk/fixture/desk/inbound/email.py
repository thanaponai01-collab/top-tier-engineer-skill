"""Mail from customers: a new thread opens a ticket, a reply lands on the ticket it answers."""
import re

from ..models import Ticket

TICKET_REF = re.compile(r"\[#(\d+)\]")


def ticket_ref(subject):
    m = TICKET_REF.search(subject or "")
    return int(m.group(1)) if m else None


def handle_new(store, sender, subject, body, now):
    t = Ticket(store.next_id(), subject, sender, channel="email", created_at=now)
    t.comments.append({"by": sender, "body": body, "at": now})
    return store.add(t)


def handle_reply(store, sender, subject, body, now):
    tid = ticket_ref(subject)
    t = store.get(tid) if tid is not None else None
    if t is None:
        return handle_new(store, sender, subject, body, now)
    t.comments.append({"by": sender, "body": body, "at": now})
    t.state = "open"
    return t


def route(store, message, now):
    sender, subject, body = message["from"], message.get("subject", ""), message.get("body", "")
    if ticket_ref(subject) is not None:
        return handle_reply(store, sender, subject, body, now)
    return handle_new(store, sender, subject, body, now)
