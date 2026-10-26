def date_str(d):
    return d.strftime("%d/%m/%Y")


def rows(orders):
    return [f"{o['id']},{date_str(o['placed_at'])}" for o in orders]
