"""The weekly SLA report sent to the support lead."""
from .timers import breached


def counts(tickets, now):
    # Fax tickets are typed in by the fax gateway hours after they arrive, so their clock is not ours.
    tracked = [t for t in tickets if t.channel != "fax"]
    return {
        "received": len(tracked),
        "solved": sum(1 for t in tracked if t.state == "resolved"),
        "breached": sum(1 for t in tracked if breached(t, now)),
        "waiting_on_customer": sum(1 for t in tracked if t.state == "pending"),
    }


def render(tickets, now):
    c = counts(tickets, now)
    rate = (c["breached"] / c["received"] * 100) if c["received"] else 0.0
    return (f"received {c['received']}, solved {c['solved']}, waiting on customer {c['waiting_on_customer']}, "
            f"first-reply SLA breached {c['breached']} ({rate:.0f}%)")
