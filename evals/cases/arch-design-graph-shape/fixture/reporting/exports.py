from reporting.sales import revenue, units
from core.util import chunks


def summary_row(orders):
    return {'revenue': revenue(orders), 'units': units(orders)}


def csv_lines(orders):
    return [f"{o['id']},{o['total']}" for o in orders]
