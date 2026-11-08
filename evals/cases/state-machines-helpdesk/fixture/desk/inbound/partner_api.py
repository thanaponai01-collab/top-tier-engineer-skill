"""Tickets pushed by partners (resellers, the fax gateway) over the partner API."""
from ..models import DeskError, Ticket

CHANNELS = ("web", "email", "fax", "phone")


def create(store, payload, now):
    channel = payload.get("channel", "web")
    if channel not in CHANNELS:
        raise DeskError(f"unknown channel {channel}")
    t = Ticket(store.next_id(), payload["subject"], payload["requester"], channel=channel, created_at=now)
    t.priority = payload.get("priority", "normal")
    t.tags.update(payload.get("tags", []))
    if payload.get("body"):
        t.comments.append({"by": payload["requester"], "body": payload["body"], "at": now})
    return store.add(t)
