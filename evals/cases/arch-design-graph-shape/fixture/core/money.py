def add(a, b):
    return a + b


def scale(cents, factor):
    return int(round(cents * factor))


def split(cents, parts):
    return [cents // parts + (1 if i < cents % parts else 0) for i in range(parts)]
