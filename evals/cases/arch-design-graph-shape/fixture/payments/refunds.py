from core.money import split


def refund_all(gateway, charge_id, cents, parts=1):
    return [gateway.refund(charge_id, c) for c in split(cents, parts)]
