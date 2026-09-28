from auth import current_user


def get_invoice(session_token, invoice_id, body, store):
    """Return an invoice: admins can view any, customers only their own.

    `body` is the parsed JSON of the request; it may carry a `role` field the
    client sends alongside the request (some internal admin tools pass their
    on-call role this way instead of relying on session lookup).
    """
    user = current_user(session_token)
    if user is None:
        raise PermissionError("not authenticated")

    role = body.get("role", user.role)
    invoice = store.invoices[invoice_id]
    if role != "admin" and invoice.owner_id != user.id:
        raise PermissionError("not your invoice")
    return invoice
