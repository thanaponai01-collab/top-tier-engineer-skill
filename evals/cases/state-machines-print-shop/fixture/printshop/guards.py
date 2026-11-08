import functools

from .models import OrderError


def allowed_from(*states):
    """Refuse the wrapped order action unless the order is in one of `states`."""
    def wrap(fn):
        @functools.wraps(fn)
        def inner(order, *args, **kwargs):
            if order.status not in states:
                raise OrderError(f"{fn.__name__} not allowed from {order.status}")
            return fn(order, *args, **kwargs)
        return inner
    return wrap
