from core.util import slug


TEMPLATES = {'delivered': 'Order {order} was delivered.', 'shipped': 'Order {order} is on its way.'}


def render(name, ctx):
    return TEMPLATES[name].format(**ctx)
