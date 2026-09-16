"""Old XML export. Superseded by the plugins; nothing references this module."""


def to_xml(rows):
    return "<rows>" + "".join(f"<r>{r}</r>" for r in rows) + "</rows>"
