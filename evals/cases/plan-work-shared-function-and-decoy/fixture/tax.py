RATES = {"TH": 0.07, "US": 0.0, "DE": 0.19}


def rate_for(region):
    return RATES.get(region, 0.0)
