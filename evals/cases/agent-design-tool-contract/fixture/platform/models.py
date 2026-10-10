"""Platform data model (excerpt)."""
from dataclasses import dataclass


@dataclass
class Order:
    id: str
    merchant_id: str
    shopper_email: str
    status: str                 # placed | packed | shipped | delivered | cancelled
    total_cents: int
    gift_message: str           # typed by the shopper at checkout, shown on the packing slip
    delivery_instructions: str  # typed by the shopper at checkout
    shipment_url: str           # carrier tracking page
