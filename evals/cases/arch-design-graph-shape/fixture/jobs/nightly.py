from reporting.exports import summary_row
from orders.history import LOG
from inventory.stock import ON_HAND


def run(orders):
    return {'summary': summary_row(orders), 'events': len(LOG), 'skus': len(ON_HAND)}
