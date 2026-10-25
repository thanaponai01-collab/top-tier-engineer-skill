"""Notes live in notes.json next to this file."""
import json, os

PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "notes.json")


class Store:
    def all(self):
        with open(PATH, encoding="utf-8") as fh:
            return json.load(fh)

    def save(self, notes):
        with open(PATH, "w", encoding="utf-8") as fh:
            json.dump(notes, fh, indent=2)

    def next_id(self):
        return max((n["id"] for n in self.all()), default=0) + 1
