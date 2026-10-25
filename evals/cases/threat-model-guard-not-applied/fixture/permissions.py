import functools

import auth


def staff_required(handler):
    @functools.wraps(handler)
    def guarded(headers, body, args):
        user = auth.current_user(headers)
        if user is None or user.role != "staff":
            raise PermissionError("staff only")
        return handler(headers, body, args)
    return guarded


def protect(module, names, check):
    """Wrap each named handler in `module` with `check`."""
    for name in names:
        setattr(module, name, check(getattr(module, name)))
