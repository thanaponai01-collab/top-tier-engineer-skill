# orders-service

Strict layering: `api/` → `services/` → `repo/` → `db.py`. Every request goes through the service
layer; nothing skips a layer. Plugins (Slack alerts etc.) hang off the service layer.
