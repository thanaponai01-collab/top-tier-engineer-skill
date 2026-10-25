"""Cross-docking: ship inbound pallets straight to outbound doors without putaway."""


def plan(order):
    door = 10 + order["id"] % 6
    return {"order": order["id"], "door": door, "skip_putaway": True}


def explain(plan_):
    return f"order {plan_['order']} cross-docks at door {plan_['door']}"
