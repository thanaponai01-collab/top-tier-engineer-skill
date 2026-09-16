"""Data layer."""
ROWS = []


def save(total):
    ROWS.append(total)
    return len(ROWS)
