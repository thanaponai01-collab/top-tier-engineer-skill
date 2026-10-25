Fixed - it now alerts. Selling 9 widgets from 12 left 3 and a LOW STOCK widget line appeared in
alerts.log; selling a gadget (40 -> 39) did not.

What was broken:
- the handlers package `__init__` never imported low_stock, so the decorator never registered it
  with the bus;
- once loaded, it listened for `stock_changed`, while the inventory emits `stock.changed`, so the
  names did not match;
- and the handler's parameter was `quantity` where the event carries `qty`. That raised a
  TypeError every time, but the bus's try/except silently ate it, which is why nothing ever showed
  up and nothing ever crashed either.
