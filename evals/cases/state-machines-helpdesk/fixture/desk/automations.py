"""Hourly automations."""
from .tickets.actions import close, solve

DAY = 24 * 3600
AUTO_CLOSE_AFTER = 4 * DAY
AUTO_SOLVE_PENDING_AFTER = 7 * DAY


def last_activity(ticket):
    times = [c["at"] for c in ticket.comments if c.get("at") is not None]
    return max(times) if times else ticket.created_at


def run(tickets, now):
    closed, solved = [], []
    for t in tickets:
        if t.state == "solved" and t.solved_at is not None and now - t.solved_at > AUTO_CLOSE_AFTER:
            close(t)
            closed.append(t.id)
        elif t.state == "pending" and now - last_activity(t) > AUTO_SOLVE_PENDING_AFTER:
            t.tags.add("auto-solved")
            solve(t, now)
            solved.append(t.id)
    return {"closed": closed, "solved": solved}
