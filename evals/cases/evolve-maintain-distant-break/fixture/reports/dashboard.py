"""The dashboard ranks orders and customers by value. It reads Order.total a lot."""
from collections import defaultdict

from money import fmt


def top_orders(orders, n=3):
    return sorted(orders, key=lambda o: o.total, reverse=True)[:n]


def by_customer(orders):
    totals = defaultdict(int)
    for o in orders:
        totals[o.customer] += o.total
    return sorted(totals.items(), key=lambda kv: kv[1], reverse=True)


def share_of_revenue(orders):
    grand = sum(o.total for o in orders) or 1
    return {o.id: round(100 * o.total / grand, 1) for o in orders}


def render(orders):
    out = ["Top orders:"]
    shares = share_of_revenue(orders)
    for o in top_orders(orders):
        out.append(f"  {o.id}  {o.customer:<10} {fmt(o.total):>10}  {shares[o.id]}%")
    out.append("Customers:")
    for customer, cents in by_customer(orders):
        out.append(f"  {customer:<10} {fmt(cents):>10}")
    return "\n".join(out)
