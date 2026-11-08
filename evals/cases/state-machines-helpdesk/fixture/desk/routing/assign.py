"""Auto-assign: hand each new ticket to the least-loaded agent who can take it now."""
from ..tickets.actions import assign

MAX_LOAD = 12


def eligible(agents):
    return [a for a in agents
            if a.presence == "available" and a.role != "viewer" and a.load < MAX_LOAD]


def auto_assign(tickets, agents):
    done = []
    for t in sorted(tickets, key=lambda t: (t.priority != "high", t.created_at)):
        if t.state != "new" or t.assignee:
            continue
        pool = eligible(agents)
        if not pool:
            break
        agent = min(pool, key=lambda a: (a.load, a.name))
        assign(t, agent)
        done.append((t.id, agent.name))
    return done
