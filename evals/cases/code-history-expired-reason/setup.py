import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
from history import build, FINAL

PROFILE_V1 = '"""Profile service: reads profiles from the profile DB, with a small cache in front."""\nimport time\n\nfrom db import profile_db\n\nPROFILE_TTL = 5  # seconds\n_cache = {}\n\n\ndef get(user_id):\n    hit = _cache.get(user_id)\n    if hit and time.time() - hit[0] < PROFILE_TTL:\n        return hit[1]\n    row = profile_db.fetch_one(user_id)\n    _cache[user_id] = (time.time(), row)\n    return row\n'
PROFILE_V2 = '"""Profile service: reads profiles from the profile DB, with a small cache in front."""\nimport time\n\nfrom db import profile_db\n\nPROFILE_TTL = 60  # seconds\n_cache = {}\n\n\ndef get(user_id):\n    hit = _cache.get(user_id)\n    if hit and time.time() - hit[0] < PROFILE_TTL:\n        return hit[1]\n    row = profile_db.fetch_one(user_id)\n    _cache[user_id] = (time.time(), row)\n    return row\n'
DASH_V1 = '"""Team dashboard: one card per teammate."""\nimport profile\n\n\ndef render(team):\n    cards = []\n    for member_id in team.member_ids:          # ~40 members on a typical team\n        p = profile.get(member_id)\n        cards.append(f"<div class=card>{p[\'name\']} - {p[\'title\']}</div>")\n    return "\\n".join(cards)\n'

build(sys.argv[1], [
    {"message": "Add profile service and team dashboard", "date": "2026-03-02T10:00:00",
      "files": {"profile.py": PROFILE_V1, "dashboard.py": DASH_V1, "db.py": FINAL, "README.md": FINAL}},
    {"message": "Raise profile cache TTL to 60s\n\nINC-212: dashboard views were saturating the profile DB.\nSee docs/incidents/INC-212.md.",
      "date": "2026-04-14T08:20:00",
      "files": {"profile.py": PROFILE_V2, "docs/incidents/INC-212.md": FINAL}},
    {"message": "Add settings page", "date": "2026-05-20T16:00:00",
      "files": {"settings_page.py": FINAL}},
    {"message": "Dashboard: one profile query per view\n\nprofile.get_many fetches all members in a single query.\nFollow-up from INC-212.",
      "date": "2026-07-30T11:45:00",
      "files": {"profile.py": FINAL, "dashboard.py": FINAL}},
    {"message": "Tidy README", "date": "2026-09-10T09:00:00", "files": {"README.md": FINAL}},
])
