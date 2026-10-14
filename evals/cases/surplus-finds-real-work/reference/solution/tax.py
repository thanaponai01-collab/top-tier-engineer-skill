RATES = {"SE": 0.25, "DE": 0.19, "FI": 0.255}


def vat(net, country):
    return round(net * RATES[country], 2)
