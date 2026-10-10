"""Settings page: shows and edits the signed-in user's own profile."""
import profile


def render(user_id):
    p = profile.get(user_id)
    return f"<form>{p['name']}</form>"
