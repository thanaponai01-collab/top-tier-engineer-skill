from shipping.flat_rate import FlatRateCalculator

CALCULATORS = {"flat": FlatRateCalculator}


def get_calculator(name):
    return CALCULATORS[name]()
