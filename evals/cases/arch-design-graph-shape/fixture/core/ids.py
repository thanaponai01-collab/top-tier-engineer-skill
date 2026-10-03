_next = {}


def new_id(prefix):
    _next[prefix] = _next.get(prefix, 0) + 1
    return f"{prefix}-{_next[prefix]:06d}"
