def render(items):
    rows = "".join(f"| {i['id']} | {i['name']} | {i['qty']} |\n" for i in items)
    return "| id | name | qty |\n|---|---|---|\n" + rows
