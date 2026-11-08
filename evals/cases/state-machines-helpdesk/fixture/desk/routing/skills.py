"""Tag-based routing hints shown to agents; auto-assign does not use them yet."""
SKILL_TAGS = {
    "billing": {"invoice", "refund", "charge"},
    "tech": {"bug", "crash", "error", "login"},
    "sales": {"quote", "pricing", "upgrade"},
}


def suggest_team(ticket):
    words = set((ticket.subject or "").lower().split()) | set(ticket.tags)
    scores = {team: len(words & tags) for team, tags in SKILL_TAGS.items()}
    best = max(scores, key=lambda k: scores[k])
    return best if scores[best] else None
