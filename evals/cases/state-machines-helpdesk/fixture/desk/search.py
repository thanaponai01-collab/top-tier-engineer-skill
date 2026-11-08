"""Agent search box: `state:open tag:billing printer jam`."""


def parse(query):
    filters, words = {}, []
    for part in query.split():
        key, sep, value = part.partition(":")
        if sep and key in ("state", "tag", "assignee", "priority", "channel"):
            filters.setdefault(key, set()).add(value)
        else:
            words.append(part.lower())
    return filters, words


def matches(ticket, filters, words):
    if "state" in filters and ticket.state not in filters["state"]:
        return False
    if "tag" in filters and not filters["tag"] & ticket.tags:
        return False
    if "assignee" in filters and ticket.assignee not in filters["assignee"]:
        return False
    if "priority" in filters and ticket.priority not in filters["priority"]:
        return False
    if "channel" in filters and ticket.channel not in filters["channel"]:
        return False
    text = (ticket.subject + " " + " ".join(c["body"] for c in ticket.comments)).lower()
    return all(w in text for w in words)


def search(tickets, query):
    filters, words = parse(query)
    return [t for t in tickets if matches(t, filters, words)]
