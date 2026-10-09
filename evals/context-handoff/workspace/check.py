from exporter import export
assert export([{"tenant_id":"t1","invoice_id":"i1","amount":4}]).startswith("tenant_id,invoice_id,amount")
print("CSV check passed")
