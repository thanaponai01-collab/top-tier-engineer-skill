"""Notes live in notes.json next to this file."""
import json, os

PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "notes.json")


def all():
    with open(PATH, encoding="utf-8") as fh:
        return json.load(fh)


def save(notes):
    with open(PATH, "w", encoding="utf-8") as fh:
        json.dump(notes, fh, indent=2)
