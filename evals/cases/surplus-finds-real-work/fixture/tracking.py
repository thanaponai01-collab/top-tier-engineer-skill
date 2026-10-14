WEIGHTS = [8, 6, 4, 2, 3, 5, 9, 7]


def check_digit(serial):
    total = sum(int(d) * w for d, w in zip(serial, WEIGHTS))
    remainder = total % 11
    return str(11 - remainder) if remainder else "0"


def tracking_number(serial):
    serial = str(serial).zfill(8)
    return serial + check_digit(serial)
