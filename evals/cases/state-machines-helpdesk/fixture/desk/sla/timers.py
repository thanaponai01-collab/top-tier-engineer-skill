"""SLA clocks: how long a ticket has waited for its first reply."""
FIRST_REPLY = {"high": 3600, "normal": 4 * 3600, "low": 24 * 3600}


def first_reply_due(ticket):
    return ticket.created_at + FIRST_REPLY.get(ticket.priority, FIRST_REPLY["normal"])


def breached(ticket, now):
    if ticket.first_reply_at is not None:
        return ticket.first_reply_at > first_reply_due(ticket)
    return now > first_reply_due(ticket)


def bump_overdue(tickets, now):
    """Unanswered tickets past their SLA go to high priority."""
    bumped = []
    for t in tickets:
        if t.state in ("new", "open") and t.first_reply_at is None and breached(t, now) and t.priority != "high":
            t.priority = "high"
            bumped.append(t.id)
    return bumped
