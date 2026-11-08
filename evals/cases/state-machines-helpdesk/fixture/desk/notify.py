"""Tell agents about their tickets on the channels they switched on."""


def channels(agent):
    out = []
    if agent.notify_desktop:
        out.append("desktop")
    if agent.notify_mobile:
        out.append("mobile")
    return out


def assigned(agent, ticket):
    return [(ch, agent.name, f"#{ticket.id} {ticket.subject} is yours") for ch in channels(agent)]
