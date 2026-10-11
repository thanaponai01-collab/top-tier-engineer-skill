"""Payment gateway client (network calls elided in this copy)."""


class Declined(Exception):
    """The card was declined. Final."""


class Transient(Exception):
    """Timeout, 5xx or rate limit. The charge may or may not have gone through."""


def charge(card_token, amount_cents, key):
    raise Transient("network elided in this copy")
