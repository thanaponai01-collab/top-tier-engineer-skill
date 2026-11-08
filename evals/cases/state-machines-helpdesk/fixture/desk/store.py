import json
import os

from .models import Ticket


class TicketStore:
    def __init__(self):
        self._tickets = {}
        self._next = 1

    def next_id(self):
        tid = self._next
        self._next += 1
        return tid

    def add(self, ticket):
        self._tickets[ticket.id] = ticket
        self._next = max(self._next, ticket.id + 1)
        return ticket

    def get(self, tid):
        return self._tickets.get(tid)

    def all(self):
        return list(self._tickets.values())

    def save(self, path):
        os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
        with open(path, "w", encoding="utf-8") as fh:
            json.dump([t.to_dict() for t in self.all()], fh, indent=1)

    @classmethod
    def load(cls, path):
        store = cls()
        if os.path.exists(path):
            with open(path, encoding="utf-8") as fh:
                for d in json.load(fh):
                    store.add(Ticket.from_dict(d))
        return store
