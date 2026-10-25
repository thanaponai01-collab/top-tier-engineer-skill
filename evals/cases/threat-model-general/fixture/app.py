"""The one entry point: handle(method, path, headers, body) -> (status, body)."""
import json

import auth
import catalog
import invoices
import orders


def _need_user(headers):
    user = auth.current_user(headers)
    if user is None:
        raise PermissionError("login required")
    return user


def r_health(headers, body, args):
    return 200, "ok"


def r_catalog(headers, body, args):
    return 200, catalog.price_list()


def r_signup(headers, body, args):
    user = auth.signup(body.get("username", ""), body.get("password", ""))
    return 201, {"id": user.id}


def r_login(headers, body, args):
    token = auth.login(body.get("username", ""), body.get("password", ""))
    return (200, {"token": token}) if token else (401, "bad credentials")


def r_order(headers, body, args):
    invoice = orders.place_order(_need_user(headers), body.get("items", []))
    return 201, {"invoice": invoice.id, "total": invoice.amount}


def r_invoice(headers, body, args):
    inv = invoices.get_invoice(_need_user(headers), int(args[0]))
    return 200, {"id": inv.id, "amount": inv.amount, "lines": inv.lines}


def r_export(headers, body, args):
    user = _need_user(headers)
    return 200, invoices.export_csv(user, int(body.get("customer_id", user.id)))


def r_refund(headers, body, args):
    return 200, {"credit": orders.refund(_need_user(headers), int(args[0]))}


ROUTES = {
    ("GET", "health"): r_health,
    ("GET", "catalog"): r_catalog,
    ("POST", "signup"): r_signup,
    ("POST", "login"): r_login,
    ("POST", "orders"): r_order,
    ("GET", "invoices"): r_invoice,
    ("POST", "invoices/export"): r_export,
    ("POST", "refunds"): r_refund,
}


def handle(method, path, headers=None, body=None):
    parts = [p for p in path.strip("/").split("/") if p]
    for n in range(len(parts), 0, -1):
        route = ROUTES.get((method, "/".join(parts[:n])))
        if route:
            try:
                return route(headers or {}, body or {}, parts[n:])
            except PermissionError as e:
                return 403, str(e)
            except (KeyError, ValueError) as e:
                return 400, str(e)
    return 404, "not found"


if __name__ == "__main__":
    print(json.dumps(handle("GET", "/catalog")))
