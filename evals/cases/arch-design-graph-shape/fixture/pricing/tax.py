from core.money import scale


def _rate(country):
    return {'US': 0.07, 'DE': 0.19}.get(country, 0.0)


def tax_for(cents, country):
    return scale(cents, _rate(country))
