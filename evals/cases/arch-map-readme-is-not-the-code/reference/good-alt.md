The diagram is in docs/architecture.md (Mermaid, renders on GitHub). Two things differ from the README:

1. The daily report doesn't follow the layers. api/reports.py imports db and runs its own SQL
   (api/reports.py:1, :7), so it bypasses services and repo. Everything else does go
   api → services → repo → db (api/orders.py:1, services/orders.py:1, repo/orders.py:1).
2. The Slack plugin (plugins/slack_notify.py) is never imported directly. plugins/__init__.py:10 loads module names from the
   ENABLED_PLUGINS list in settings.py with importlib. I drew that arrow dashed and marked it as
   inferred from config, since there's no import to point at.

Each arrow in the file has its file:line in a table under the diagram. The map is accurate as of
today's code. If someone moves the report query into services, redraw that one arrow.
