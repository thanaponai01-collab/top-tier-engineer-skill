from app.util.text import plural


def summary(items):
    total = sum(i["qty"] for i in items)
    empty = [i["name"] for i in items if i["qty"] == 0]
    line = f"{len(items)} {plural('item', len(items))}, {total} in stock"
    return line + (f"; out of stock: {', '.join(empty)}" if empty else "")
