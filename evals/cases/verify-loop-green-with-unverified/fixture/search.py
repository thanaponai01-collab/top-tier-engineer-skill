CATALOG = ["red shirt", "blue shirt", "red hat"]


def search(term):
    term = term.lower()
    return [name for name in CATALOG if term in name]
