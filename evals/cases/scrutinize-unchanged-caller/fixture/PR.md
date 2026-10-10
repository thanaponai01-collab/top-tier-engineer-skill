# Make get_user return None for unknown users

Raising KeyError for a missing user is awkward: every caller needs a try/except. This returns None
instead, and updates the profile page to match. Pure refactor, no behaviour change for known users.
Tests are green (`python -m unittest discover -s tests`).
