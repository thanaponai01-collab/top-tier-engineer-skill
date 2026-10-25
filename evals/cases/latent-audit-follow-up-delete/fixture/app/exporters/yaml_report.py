def render(items):
    return "".join(f"- id: {i['id']}\n  name: {i['name']}\n  qty: {i['qty']}\n" for i in items)
