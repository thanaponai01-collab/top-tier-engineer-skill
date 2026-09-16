# Wire Check — fixture/

I walked the imports from `app.py`.

Two modules are orphaned: `handlers/export.py` and `handlers/digest.py`.
Neither is reachable from the route table, so both are dead weight.
Recommend you delete handlers/digest.py and wire export up if you still want it.
