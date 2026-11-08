"""Agent presence, driven by the desk app's heartbeat."""
TIMEOUT = 300


def go_online(agent, now):
    agent.presence = "online"
    agent.last_seen = now


def go_away(agent, now):
    if agent.presence == "offline":
        return
    agent.presence = "away"
    agent.last_seen = now


def go_offline(agent):
    agent.presence = "offline"


def heartbeat(agent, now):
    if agent.presence == "offline":
        return
    agent.last_seen = now


def sweep(agents, now):
    """Agents whose app stopped sending heartbeats drop offline."""
    dropped = []
    for a in agents:
        if a.presence != "offline" and now - a.last_seen > TIMEOUT:
            go_offline(a)
            dropped.append(a.name)
    return dropped
