def fmt_date(d):
    return d.strftime("%d/%m/%Y")


def order_page(order):
    return f"Order {order['id']} placed {fmt_date(order['placed_at'])}"
