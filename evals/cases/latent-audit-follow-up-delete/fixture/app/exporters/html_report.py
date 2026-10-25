from html import escape


def render(items):
    rows = "".join(f"<tr><td>{i['id']}</td><td>{escape(i['name'])}</td><td>{i['qty']}</td></tr>" for i in items)
    return f"<table>{rows}</table>\n"
