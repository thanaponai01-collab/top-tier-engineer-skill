def render(items):
    return "id\tname\tqty\n" + "".join(f"{i['id']}\t{i['name']}\t{i['qty']}\n" for i in items)
