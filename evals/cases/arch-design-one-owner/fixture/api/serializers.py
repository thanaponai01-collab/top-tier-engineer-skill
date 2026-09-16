def format_date(d):
    return d.strftime("%d/%m/%Y")


def order_json(order):
    return {"id": order["id"], "placed_at": format_date(order["placed_at"])}
