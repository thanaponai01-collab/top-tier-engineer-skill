from core.money import scale


RATES = {'USD': 1.0, 'EUR': 0.92, 'GBP': 0.79}


def convert(cents, to):
    return scale(cents, RATES[to])
