from core.util import clamp
from core.money import scale


CODES = {'WELCOME10': 0.10, 'VIP20': 0.20}


def percent_off(code):
    return clamp(CODES.get(code, 0.0), 0.0, 0.5)


def apply_code(cents, code):
    return cents - scale(cents, percent_off(code))
