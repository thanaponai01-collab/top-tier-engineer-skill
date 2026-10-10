"""User lookup."""

_USERS = {
    "u1": {"id": "u1", "name": "Ada", "tier": "gold"},
    "u2": {"id": "u2", "name": "Linus", "tier": "silver"},
}


def get_user(user_id):
    """Return the user, or None if there is none."""
    return _USERS.get(user_id)
