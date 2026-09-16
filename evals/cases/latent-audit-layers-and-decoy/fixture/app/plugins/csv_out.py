"""Output plugin. No import statement mentions this module."""


def render(rows):
    return "\n".join(str(r) for r in rows)
