class Invoice:
    def __init__(self, id, owner_id, amount):
        self.id = id
        self.owner_id = owner_id
        self.amount = amount


class Store:
    def __init__(self):
        self.invoices = {
            10: Invoice(id=10, owner_id=1, amount=42.50),
            11: Invoice(id=11, owner_id=2, amount=999.00),
        }
