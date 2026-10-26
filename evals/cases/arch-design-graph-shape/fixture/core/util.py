def clamp(x, lo, hi):
    return max(lo, min(hi, x))


def as_cents(amount):
    return int(round(amount * 100))


def slug(text):
    return '-'.join(text.lower().split())


def chunks(seq, n):
    return [seq[i:i + n] for i in range(0, len(seq), n)]


def first(seq, default=None):
    return seq[0] if seq else default
