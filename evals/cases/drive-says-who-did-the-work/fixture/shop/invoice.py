"""Plain-text invoice for a cart."""
from shop import catalog


def cents(n):
    return f"{n // 100}.{n % 100:02d}"


def render(cart):
    out = []
    for sku, qty in sorted(cart.lines.items()):
        out.append(f"{catalog.name(sku):<12} x{qty:<3} {cents(cart.line_total(sku)):>9}")
    out.append(f"{'Total':<17} {cents(cart.subtotal()):>9}")
    return "\n".join(out)
