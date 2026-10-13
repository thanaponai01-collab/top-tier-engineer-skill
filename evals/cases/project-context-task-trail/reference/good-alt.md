Today's decision accepts at most 500, while the implementation accepts 1000 (brief/export.md, app.py).
The earlier commit capped allocations on small customer machines. It explains the old behavior,
not the latest requirement. The current unittest check is red. evidence/export.md records an older pass.
work/export.md leaves the rejection message unresolved. Implementation should begin with the boundary,
keeping that question open; this investigation left the working tree alone. The billing
reconciliation job in `src/billing/reconcile.py` also calls `export_allowed`, so it shares the
boundary being changed.
