"""Team dashboard: one card per teammate."""
import profile


def render(team):
    people = profile.get_many(team.member_ids)
    return "\n".join(f"<div class=card>{p['name']} - {p['title']}</div>" for p in people)
