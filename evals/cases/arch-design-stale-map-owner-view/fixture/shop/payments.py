import uuid


def charge(card_token, amount):
    return "ch_" + uuid.uuid4().hex[:8]


def refund(charge_id, amount):
    return {"charge_id": charge_id, "amount": amount}
