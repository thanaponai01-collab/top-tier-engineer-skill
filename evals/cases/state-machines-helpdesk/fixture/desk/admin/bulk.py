"""Bulk actions from the admin screen."""
from ..auth import require
from ..tickets.actions import close


def bulk_close(admin, tickets):
    require(admin, "bulk")
    done = []
    for t in tickets:
        if t.state == "solved":
            close(t)
            done.append(t.id)
    return done


def bulk_tag(admin, tickets, tag):
    require(admin, "bulk")
    for t in tickets:
        t.tags.add(tag)
    return len(tickets)


def bulk_priority(admin, tickets, priority):
    require(admin, "bulk")
    if priority not in ("low", "normal", "high"):
        raise ValueError(priority)
    for t in tickets:
        t.priority = priority
    return len(tickets)
