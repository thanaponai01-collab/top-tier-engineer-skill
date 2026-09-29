from dataclasses import dataclass, field


@dataclass
class Customer:
    id: str
    name: str
    region: str = "TH"


@dataclass
class Line:
    sku: str
    qty: int
    unit_price_cents: int


@dataclass
class Invoice:
    id: str
    customer: Customer
    lines: list = field(default_factory=list)
