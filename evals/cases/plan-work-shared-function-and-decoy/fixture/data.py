from models import Customer, Invoice, Line

SOMCHAI = Customer("c1", "Somchai", "TH")
ACME = Customer("c2", "Acme Inc", "US")
HANS = Customer("c3", "Hans GmbH", "DE")

INVOICES = [
    Invoice("inv-1", SOMCHAI, [Line("pen", 10, 500), Line("ink", 2, 2500)]),
    Invoice("inv-2", ACME, [Line("desk", 1, 120000)]),
    Invoice("inv-3", HANS, [Line("lamp", 3, 4000)]),
]
