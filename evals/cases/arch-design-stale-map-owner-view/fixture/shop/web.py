from shop.checkout import place_order


def handle_checkout(request):
    order = place_order(request["customer"], request["cart"])
    return {"status": 201, "order_id": order["id"]}
