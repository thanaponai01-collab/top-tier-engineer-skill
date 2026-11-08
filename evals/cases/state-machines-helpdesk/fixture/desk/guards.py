import functools

from .models import DeskError


def from_states(*states):
    """Refuse the wrapped ticket action unless the ticket is in one of `states`."""
    def wrap(fn):
        @functools.wraps(fn)
        def inner(ticket, *args, **kwargs):
            if ticket.state not in states:
                raise DeskError(f"{fn.__name__}: ticket {ticket.id} is {ticket.state}")
            return fn(ticket, *args, **kwargs)
        return inner
    return wrap
