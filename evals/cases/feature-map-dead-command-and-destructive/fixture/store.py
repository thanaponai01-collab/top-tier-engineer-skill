"""Notes live in notes.json next to this file."""
import json, os

PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "notes.json")


class Store:
    def all(self):
        with open(PATH) as fh:
            return json.load(fh)

    def save(self, notes):
        with open(PATH, "w") as fh:
            json.dump(notes, fh, indent=2)
