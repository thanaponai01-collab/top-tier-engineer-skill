from core.util import first


BOOK = {}


def add_address(cid, line1, city, country):
    BOOK.setdefault(cid, []).append({'line1': line1, 'city': city, 'country': country})


def default_address(cid):
    return first(BOOK.get(cid, []))
