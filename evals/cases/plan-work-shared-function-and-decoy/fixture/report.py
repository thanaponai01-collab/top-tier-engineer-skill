from data import INVOICES
from invoice import total


def render(invoices):
    return "\n".join(f"{i.id:<6} {i.customer.name:<10} {total(i) / 100:>10.2f}" for i in invoices)


if __name__ == "__main__":
    print(render(INVOICES))
