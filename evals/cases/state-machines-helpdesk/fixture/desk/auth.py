"""Who may do what. Roles: admin, agent, viewer (read-only seats for managers)."""
from .models import DeskError

CAN = {
    "admin": {"read", "reply", "assign", "solve", "bulk", "manage"},
    "agent": {"read", "reply", "assign", "solve"},
    "viewer": {"read"},
}


def require(agent, action):
    if action not in CAN.get(agent.role, set()):
        raise DeskError(f"{agent.name} ({agent.role}) may not {action}")


def promote(admin, agent):
    require(admin, "manage")
    if agent.role == "viewer":
        agent.role = "agent"
    elif agent.role == "agent":
        agent.role = "admin"


def demote(admin, agent):
    require(admin, "manage")
    if agent.role == "admin":
        agent.role = "agent"
    elif agent.role == "agent":
        agent.role = "viewer"
