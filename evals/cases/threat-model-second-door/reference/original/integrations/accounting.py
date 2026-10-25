"""Nightly sync: the accounting system pulls each customer's invoices as CSV, logged in as staff."""
import auth
import invoices
from routes import route


@route("POST", "integrations/accounting/pull")
def pull(headers, body, args):
    user = auth.current_user(headers)
    if user is None:
        raise PermissionError("login required")
    return 200, invoices.export_csv(user, int(body["customer_id"]))
