"""Paper stock: checkout reserves the pages an order needs, cancel gives them back."""

CAPACITY = 1000
_reserved = 0


class OutOfPaper(Exception):
    pass


def reserve(pages):
    global _reserved
    if _reserved + pages > CAPACITY:
        raise OutOfPaper(f"only {CAPACITY - _reserved} pages left")
    _reserved += pages


def release(pages):
    global _reserved
    _reserved = max(0, _reserved - pages)


def available():
    return CAPACITY - _reserved


def reset():
    global _reserved
    _reserved = 0
