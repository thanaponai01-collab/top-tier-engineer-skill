"""Jobs we gave up on. Ops reviews this list every morning and retries by hand."""
_dead = []


def put(job, reason):
    _dead.append({"job": job, "reason": reason})
