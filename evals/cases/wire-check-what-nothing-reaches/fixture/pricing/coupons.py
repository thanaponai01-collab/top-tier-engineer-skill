CODES = {"SPRING10": 0.10, "VIP25": 0.25}


def apply(amount, code):
    return round(amount * (1 - CODES.get(code.upper(), 0)), 2)
