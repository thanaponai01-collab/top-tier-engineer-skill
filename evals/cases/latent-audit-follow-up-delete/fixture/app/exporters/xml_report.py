from xml.sax.saxutils import escape


def render(items):
    rows = "".join(f'  <item id="{i["id"]}" qty="{i["qty"]}">{escape(i["name"])}</item>\n'
                   for i in items)
    return f"<items>\n{rows}</items>\n"
