"""Entry point: python main.py <path>"""
import sys

from api import orders, reports
import plugins

ROUTES = {
    "/orders": orders.list_orders,
    "/orders/new": orders.create_order,
    "/reports/daily": reports.daily_totals,
}

if __name__ == "__main__":
    plugins.load_enabled()
    print(ROUTES[sys.argv[1]]())
