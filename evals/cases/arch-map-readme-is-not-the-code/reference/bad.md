# Architecture

Saved to ARCHITECTURE.md:

api/ → services/ → repo/ → db.py, plus plugins hanging off services/.

Every request goes through the service layer, so the layering is clean. The Slack plugin is wired from
the service layer as well.
