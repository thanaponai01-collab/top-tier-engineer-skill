"""Everything an agent can do to a ticket."""
from ..guards import from_states
from ..models import DeskError


def assign(ticket, agent):
    if ticket.state not in ("new", "open"):
        raise DeskError(f"cannot assign a ticket that is {ticket.state}")
    if ticket.assignee and ticket.assignee != agent.name:
        raise DeskError(f"ticket {ticket.id} already belongs to {ticket.assignee}")
    ticket.assignee = agent.name
    agent.load += 1
    ticket.state = "open"


def reply(ticket, agent, body, now):
    if ticket.state in ("solved", "closed"):
        raise DeskError("reopen the ticket before replying")
    ticket.comments.append({"by": agent.name, "body": body, "at": now})
    if ticket.first_reply_at is None:
        ticket.first_reply_at = now


def set_pending(ticket):
    if ticket.state != "open":
        raise DeskError(f"only open tickets can wait on the customer, not {ticket.state}")
    ticket.state = "pending"


def customer_replied(ticket, body, now):
    ticket.comments.append({"by": ticket.requester, "body": body, "at": now})
    if ticket.state == "pending":
        ticket.state = "open"


def solve(ticket, now):
    if ticket.state not in ("open", "pending"):
        raise DeskError(f"cannot solve a ticket that is {ticket.state}")
    ticket.state = "solved"
    ticket.solved_at = now


def close(ticket):
    if ticket.state != "solved":
        raise DeskError(f"only solved tickets close, not {ticket.state}")
    ticket.state = "closed"


@from_states("solved")
def reopen(ticket):
    ticket.state = "open"
    ticket.solved_at = None


def escalate(ticket, reason):
    if ticket.state != "open":
        raise DeskError(f"only open tickets escalate, not {ticket.state}")
    ticket.tags.add("escalated")
    ticket.comments.append({"by": "system", "body": f"escalated: {reason}", "at": None})
    ticket.state = "escalated"


def take(ticket, agent):
    """A senior agent takes a ticket off the queue and owns it from then on."""
    if not agent.senior:
        raise DeskError(f"{agent.name} is not a senior agent")
    if ticket.state not in ("new", "open"):
        raise DeskError(f"cannot take a ticket that is {ticket.state}")
    ticket.assignee = agent.name
    agent.load += 1
    ticket.state = "open"
