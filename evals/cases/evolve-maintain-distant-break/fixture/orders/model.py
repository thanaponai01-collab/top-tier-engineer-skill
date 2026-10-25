"""Orders and their lines. Amounts are integer cents."""


class Line:
    def __init__(self, id, sku, price_cents, qty):
        self.id = id
        self.sku = sku
        self.price_cents = price_cents
        self.qty = qty

    def subtotal(self):
        return self.price_cents * self.qty

    def to_dict(self):
        return {"id": self.id, "sku": self.sku, "price_cents": self.price_cents, "qty": self.qty}


class Order:
    def __init__(self, id, customer, lines, status="open"):
        self.id = id
        self.customer = customer
        self.lines = lines
        self.status = status

    @property
    def total(self):
        # Recomputed on every access.
        return sum(line.subtotal() for line in self.lines)

    def add_line(self, line):
        self.lines.append(line)

    def line(self, line_id):
        for line in self.lines:
            if line.id == line_id:
                return line
        raise KeyError(line_id)

    def to_dict(self):
        return {"id": self.id, "customer": self.customer, "status": self.status,
                "lines": [line.to_dict() for line in self.lines]}

    @classmethod
    def from_dict(cls, d):
        d = dict(d)
        d["lines"] = [Line(**line) for line in d["lines"]]
        return cls(**d)
