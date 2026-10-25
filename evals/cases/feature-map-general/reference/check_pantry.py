"""Grader: the person's pantry survived both sessions."""
import json, sys

data = json.load(open("pantry.json", encoding="utf-8"))
names = {i["name"] for i in data.get("items", [])}
kept = names >= {"Rice", "Eggs", "Olive oil", "Coffee"}
print("ALL-OK" if kept else f"NOT-OK: {sorted(names)}")
sys.exit(0 if kept else 1)
