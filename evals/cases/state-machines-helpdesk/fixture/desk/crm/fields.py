"""How desk fields map onto CRM fields."""
STATE_TO_CRM = {
    "new": "Open",
    "open": "Open",
    "pending": "Waiting",
    "escalated": "Open",
    "solved": "Closed",
    "closed": "Closed",
}
PRIORITY_TO_CRM = {"low": 3, "normal": 2, "high": 1}


def to_crm(ticket_dict):
    return {
        "external_id": f"desk-{ticket_dict['id']}",
        "status": STATE_TO_CRM.get(ticket_dict["state"], "Open"),
        "priority": PRIORITY_TO_CRM.get(ticket_dict["priority"], 2),
        "contact": ticket_dict["requester"],
    }
