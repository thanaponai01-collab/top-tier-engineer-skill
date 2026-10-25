"""Price one order: line totals, discounts, shipping and tax."""


def compute_price(order, customer, today):
    total = 0.0
    for line in order["lines"]:
        price = line["unit_price"] * line["qty"]
        if line.get("kind") == "service":
            if customer.get("contract"):
                if customer["contract"].get("rate"):
                    price = customer["contract"]["rate"] * line["qty"]
                else:
                    if line["qty"] > 10:
                        price = price * 0.9
            elif line["qty"] > 20:
                price = price * 0.95
        elif line.get("kind") == "goods":
            if line.get("bulk"):
                if line["qty"] >= 100:
                    price = price * 0.8
                elif line["qty"] >= 50:
                    price = price * 0.85
                else:
                    price = price * 0.9
            if line.get("clearance") and not customer.get("wholesale"):
                price = price * 0.5
        else:
            if line.get("kind") == "gift":
                price = 0.0
        total += price

    if order.get("coupon"):
        code = order["coupon"]
        if code.startswith("SAVE") and total > 50:
            total -= float(code[4:] or 0)
        elif code == "FIRST" and customer.get("orders", 0) == 0:
            total = total * 0.85
        elif code == "VIP" and customer.get("vip"):
            if today.month == 12:
                total = total * 0.75
            else:
                total = total * 0.8

    if order.get("ship"):
        if customer.get("country") == "US":
            if total < 35:
                total += 5.99
        elif customer.get("country") in ("CA", "MX"):
            total += 12.0
        else:
            if order.get("express"):
                total += 40.0
            else:
                total += 25.0

    if customer.get("tax_exempt"):
        return round(total, 2)
    if customer.get("country") == "US":
        if customer.get("state") in ("OR", "MT", "NH", "DE"):
            rate = 0.0
        else:
            rate = 0.07
    elif customer.get("country") == "CA":
        rate = 0.13
    else:
        rate = 0.2
    return round(total * (1 + rate), 2)
