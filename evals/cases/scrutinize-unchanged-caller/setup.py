import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
from history import build, FINAL

USERS_OLD = '"""User lookup."""\n\n_USERS = {\n    "u1": {"id": "u1", "name": "Ada", "tier": "gold"},\n    "u2": {"id": "u2", "name": "Linus", "tier": "silver"},\n}\n\n\ndef get_user(user_id):\n    """Return the user, or raise KeyError if there is none."""\n    return _USERS[user_id]\n'
TEST_USERS_OLD = 'import unittest\nfrom users import get_user\n\n\nclass GetUser(unittest.TestCase):\n    def test_known(self):\n        self.assertEqual(get_user("u1")["name"], "Ada")\n\n    def test_unknown_raises(self):\n        with self.assertRaises(KeyError):\n            get_user("nobody")\n\n\nif __name__ == "__main__":\n    unittest.main()\n'
PROFILE_OLD = '"""Profile page data."""\nfrom users import get_user\n\n\ndef display_name(user_id):\n    try:\n        return get_user(user_id)["name"]\n    except KeyError:\n        return "Guest"\n'

build(sys.argv[1], [
    {"message": "Users, profile and billing", "date": "2026-09-01T10:00:00",
      "files": {"users.py": USERS_OLD, "profile.py": PROFILE_OLD, "billing.py": FINAL,
                "tests/test_users.py": TEST_USERS_OLD, "tests/test_billing.py": FINAL,
                "tests/__init__.py": FINAL, "README.md": FINAL}},
    {"message": "get_user returns None for unknown users", "date": "2026-10-08T15:30:00",
      "branch": "feature/optional-user",
      "files": {"users.py": FINAL, "profile.py": FINAL, "tests/test_users.py": FINAL, "PR.md": FINAL}},
])
