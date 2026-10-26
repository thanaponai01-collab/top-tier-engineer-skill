# Architecture Audit — fixture/

Found major duplication: four date formatters scattered across the codebase.

`web/views.py`, `api/serializers.py`, `jobs/export.py` and `billing/invoice.py`
all format dates independently. Consolidate all four into a single
`utils/dates.py` helper and have every module call it. That removes the
duplication in one move.
